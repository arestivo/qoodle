# Specification: Question Variant Generation

## Overview

Generate multiple variants of question templates by substituting variable placeholders with randomly generated values. Uses seeded random generation for deterministic, reproducible results based on template ID and version number.

## Purpose

- Create diverse exam versions from single templates
- Prevent cheating through question variation
- Ensure reproducible generation (same seed = same output)
- Support variable substitution in question text and answer choices

## ADDED Requirements

### Requirement: Variable Substitution Engine

Generate question variants by replacing `{{variable}}` markers with randomly generated values.

#### Variable Marker Format
- Pattern: `{{variable_name}}`
- Location: QuestionTemplate.text and Choice.text (JSONField content)
- Example: `"What is {{number}} + {{number}}?"`

#### Seed Generation
Use deterministic seed based on template and version:
```python
seed = hash(f"{template.id}_{version_number}")
```

This ensures:
- Same template + version = same output
- Different versions = different values
- Reproducible across exports

#### Scenario: Generate variant with number variables
- **GIVEN** template text: "Calculate {{number}} + {{number}}"
- **AND** template variables: `{"number": {"type": "integer", "min": 1, "max": 10}}`
- **AND** version_number=0
- **WHEN** generate_variant() is called
- **THEN** returns text with numbers substituted (e.g., "Calculate 5 + 3")
- **AND** values are within specified range [1, 10]
- **AND** calling again with version=0 returns same values

#### Scenario: Generate different variants
- **GIVEN** template text: "What is {{x}} * {{y}}?"
- **AND** variables: `{"x": {"type": "integer", "min": 2, "max": 9}, "y": ...}`
- **WHEN** generate_variant(version=0) is called
- **THEN** returns variant #0 (e.g., "What is 4 * 7?")
- **WHEN** generate_variant(version=1) is called
- **THEN** returns variant #1 with different values (e.g., "What is 3 * 9?")
- **AND** variant #1 ≠ variant #0

### Requirement: Variant Uniqueness Validation

Ensure generated variants are unique (no duplicate question text).

#### Uniqueness Check
After generating all variants for a template:
1. Compare rendered text of all variants
2. If duplicates found, increment seed and regenerate
3. Retry up to MAX_ATTEMPTS (default: 50)
4. If still duplicates, raise error

#### Scenario: Generate unique variants
- **GIVEN** template with 5 versions requested
- **AND** variable range allows sufficient uniqueness
- **WHEN** generate_all_variants() is called
- **THEN** returns 5 variants
- **AND** all variant texts are unique
- **AND** no two variants have identical rendered text

#### Scenario: Fail to generate unique variants
- **GIVEN** template: "Pick {{choice}}" with variable: `{"choice": {"type": "choice", "options": ["A", "B"]}}`
- **AND** number_of_versions=10 (more than 2 possible values)
- **WHEN** generate_all_variants() is called
- **THEN** raises ValueError: "Unable to generate 10 unique variants for template '{title}' after 50 attempts"

### Requirement: Variable Type Support

Support multiple variable types with appropriate random generation.

#### Type: Integer
```json
{
  "variable_name": {
    "type": "integer",
    "min": 1,
    "max": 100
  }
}
```

Generates random integer in range [min, max] inclusive.

#### Type: Float
```json
{
  "variable_name": {
    "type": "float",
    "min": 0.0,
    "max": 1.0,
    "decimals": 2
  }
}
```

Generates random float rounded to specified decimals.

#### Type: Choice
```json
{
  "variable_name": {
    "type": "choice",
    "options": ["red", "blue", "green"]
  }
}
```

Randomly selects one option from the list.

#### Scenario: Substitute integer variable
- **GIVEN** text: "Solve {{n}} + 5"
- **AND** variables: `{"n": {"type": "integer", "min": 10, "max": 20}}`
- **WHEN** substitute_variables() is called with seed=12345
- **THEN** returns text like "Solve 15 + 5"
- **AND** 10 ≤ substituted value ≤ 20

#### Scenario: Substitute choice variable
- **GIVEN** text: "What color is {{color}}?"
- **AND** variables: `{"color": {"type": "choice", "options": ["red", "blue"]}}`
- **WHEN** substitute_variables() is called
- **THEN** returns either "What color is red?" or "What color is blue?"

### Requirement: Choice Text Variable Substitution

Apply variable substitution to answer choice text as well as question text.

#### Process
For each choice in template:
1. Extract choice text in target language
2. Apply same variable substitution as question text
3. Use same seed/random state for consistency
4. Render markdown to HTML

#### Scenario: Substitute variables in choices
- **GIVEN** question: "Calculate {{x}} + {{y}}"
- **AND** choice texts: "{{x}}", "{{y}}", "{{x}} + {{y}}", "0"
- **AND** seed generates x=5, y=3
- **WHEN** variant is generated
- **THEN** question text: "Calculate 5 + 3"
- **AND** choice 1: "5"
- **AND** choice 2: "3"
- **AND** choice 3: "8"
- **AND** choice 4: "0" (no variables)

### Requirement: No-Variable Template Handling

Handle templates without variables gracefully.

#### Scenario: Generate variant from template without variables
- **GIVEN** template text: "What is HTML?"
- **AND** variables: `{}` (empty)
- **AND** number_of_versions=5
- **WHEN** generate_all_variants() is called
- **THEN** returns 5 identical variants
- **AND** all have same text: "What is HTML?"
- **AND** no uniqueness error (templates without variables allowed to be identical)

## Implementation

### Location
`apps/exams/variant_generation.py`

### Main Generation Function

```python
from typing import Dict, List, Any
import random
import hashlib

def generate_variant(
    template: QuestionTemplate,
    version_number: int,
    language: str
) -> Dict[str, str]:
    """
    Generate a single question variant.
    
    Args:
        template: QuestionTemplate instance
        version_number: Variant index (0-based)
        language: Target language code
        
    Returns:
        Dict with 'question_text' and 'choices' (list of rendered texts)
    """
    # Generate deterministic seed
    seed_str = f"{template.id}_{version_number}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**32)
    random.seed(seed)
    
    # Extract variables from template
    variables = template.variables or {}
    
    # Generate variable values
    variable_values = {}
    for var_name, var_config in variables.items():
        variable_values[var_name] = generate_variable_value(var_config)
    
    # Substitute in question text
    question_text = extract_language_text(template.text, language)
    question_text = substitute_markers(question_text, variable_values)
    
    # Substitute in choices
    choice_texts = []
    for choice in template.choices.order_by('order'):
        choice_text = extract_language_text(choice.text, language)
        choice_text = substitute_markers(choice_text, variable_values)
        choice_texts.append(choice_text)
    
    return {
        'question_text': question_text,
        'choices': choice_texts
    }

def generate_variable_value(config: Dict[str, Any]) -> Any:
    """Generate random value based on variable config."""
    var_type = config['type']
    
    if var_type == 'integer':
        return random.randint(config['min'], config['max'])
    
    elif var_type == 'float':
        value = random.uniform(config['min'], config['max'])
        decimals = config.get('decimals', 2)
        return round(value, decimals)
    
    elif var_type == 'choice':
        return random.choice(config['options'])
    
    else:
        raise ValueError(f"Unsupported variable type: {var_type}")

def substitute_markers(text: str, values: Dict[str, Any]) -> str:
    """Replace {{var}} markers with actual values."""
    result = text
    for var_name, value in values.items():
        marker = f"{{{{{var_name}}}}}"  # {{var_name}}
        result = result.replace(marker, str(value))
    return result
```

### Uniqueness Validation

```python
def generate_all_variants(
    template: QuestionTemplate,
    num_versions: int,
    language: str,
    max_attempts: int = 50
) -> List[Dict[str, str]]:
    """
    Generate all unique variants for a template.
    
    Args:
        template: QuestionTemplate instance
        num_versions: Number of variants to generate
        language: Target language code
        max_attempts: Max retries for uniqueness
        
    Returns:
        List of variant dicts
        
    Raises:
        ValueError: If unable to generate unique variants
    """
    # Templates without variables can have duplicates
    if not template.variables:
        return [
            generate_variant(template, i, language)
            for i in range(num_versions)
        ]
    
    # Try to generate unique variants
    for attempt in range(max_attempts):
        variants = []
        seen_texts = set()
        
        for version in range(num_versions):
            variant = generate_variant(template, version + attempt, language)
            text = variant['question_text']
            
            if text in seen_texts:
                break  # Duplicate found, retry with different seed offset
            
            seen_texts.add(text)
            variants.append(variant)
        
        # Success if all unique
        if len(variants) == num_versions:
            return variants
    
    # Failed to generate unique variants
    raise ValueError(
        f"Unable to generate {num_versions} unique variants for template "
        f"'{template.title}' after {max_attempts} attempts. "
        f"Consider reducing number_of_versions or expanding variable ranges."
    )
```

## Testing

### Location
`apps/exams/tests_variant_generation.py`

### Test Coverage

```python
class VariantGenerationTests(TestCase):
    """Tests for question variant generation."""
    
    def test_generate_variant_with_integer(self):
        """Test variant generation with integer variable."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Math Question",
            text={"content": "==en==Calculate {{n}} + 5"},
            variables={"n": {"type": "integer", "min": 1, "max": 10}}
        )
        
        variant = generate_variant(template, version_number=0, language='en')
        
        self.assertIn('Calculate ', variant['question_text'])
        self.assertIn(' + 5', variant['question_text'])
        # Extract number and verify range
        number = int(variant['question_text'].split()[1])
        self.assertGreaterEqual(number, 1)
        self.assertLessEqual(number, 10)
    
    def test_generate_variant_deterministic(self):
        """Test that same version generates same output."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Test",
            text={"content": "==en=={{x}}"},
            variables={"x": {"type": "integer", "min": 1, "max": 100}}
        )
        
        variant1 = generate_variant(template, 0, 'en')
        variant2 = generate_variant(template, 0, 'en')
        
        self.assertEqual(variant1['question_text'], variant2['question_text'])
    
    def test_generate_different_variants(self):
        """Test that different versions generate different output."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Test",
            text={"content": "==en=={{x}}"},
            variables={"x": {"type": "integer", "min": 1, "max": 100}}
        )
        
        variant0 = generate_variant(template, 0, 'en')
        variant1 = generate_variant(template, 1, 'en')
        
        # Very high probability they're different with range 1-100
        self.assertNotEqual(variant0['question_text'], variant1['question_text'])
    
    def test_generate_all_variants_unique(self):
        """Test generating multiple unique variants."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Test",
            text={"content": "==en=={{x}} * {{y}}"},
            variables={
                "x": {"type": "integer", "min": 1, "max": 10},
                "y": {"type": "integer", "min": 1, "max": 10}
            }
        )
        
        variants = generate_all_variants(template, num_versions=5, language='en')
        
        self.assertEqual(len(variants), 5)
        texts = [v['question_text'] for v in variants]
        self.assertEqual(len(texts), len(set(texts)))  # All unique
    
    def test_generate_fails_with_insufficient_uniqueness(self):
        """Test error when can't generate enough unique variants."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Test",
            text={"content": "==en=={{choice}}"},
            variables={"choice": {"type": "choice", "options": ["A", "B"]}}
        )
        
        with self.assertRaises(ValueError) as ctx:
            generate_all_variants(template, num_versions=10, language='en')
        
        self.assertIn('Unable to generate 10 unique variants', str(ctx.exception))
    
    def test_substitute_in_choices(self):
        """Test variable substitution in answer choices."""
        template = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Test",
            text={"content": "==en=={{x}} + {{y}}"},
            variables={
                "x": {"type": "integer", "min": 1, "max": 5},
                "y": {"type": "integer", "min": 1, "max": 5}
            }
        )
        Choice.objects.create(
            question=template,
            order=0,
            text={"content": "==en=={{x}}"}
        )
        Choice.objects.create(
            question=template,
            order=1,
            text={"content": "==en=={{y}}"}
        )
        
        variant = generate_variant(template, 0, 'en')
        
        self.assertEqual(len(variant['choices']), 2)
        # Choices should have same variable values as question
        question_parts = variant['question_text'].split(' + ')
        self.assertEqual(variant['choices'][0], question_parts[0])
        self.assertEqual(variant['choices'][1], question_parts[1])
```

## Dependencies

- [multilingual-questions](../../../specs/multilingual-questions/spec.md) - Language extraction
- [exam-management](../../specs/exam-management/spec.md) - QuestionPoolTemplate.number_of_versions

## Related Specifications

- [moodle-xml-export](../moodle-xml-export/spec.md) - Uses variant generation for export
