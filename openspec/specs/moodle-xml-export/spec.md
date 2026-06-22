# Specification: Moodle XML Export

## Overview

Export exam questions to Moodle XML format for importing into Moodle quiz banks. Generates valid Moodle 4.x XML with question variants, language-specific content, markdown-to-HTML conversion, and CDATA wrapping for special characters.

## Purpose

- Generate Moodle-compatible XML files from exam specifications
- Apply grading mode (single/multi choice) with custom fraction schemes
- Convert multilingual markdown content to HTML
- Enable teachers to import exams directly into Moodle

## Data Models

### Location
`apps/exams/models.py`

### Modified: Exam Model

```python
class Exam(UUIDModel):
    """An exam composed of ordered question pools."""
    
    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    grading_mode = models.CharField(
        max_length=10,
        choices=[
            ('single', 'Single Choice'),
            ('multi', 'Multiple Choice'),
        ],
        default='single',
        help_text="Single: one correct answer. Multi: allows partial credit tracking."
    )
```

### Modified: QuestionPool Model

```python
class QuestionPool(UUIDModel):
    """Ordered pool of question templates within an exam."""
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='pools')
    order = models.PositiveIntegerField()
    default_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(Decimal('0.1'))],
        help_text="Point value for questions in this pool (default: 1.0)"
    )
```
## Requirements
### Requirement: Export View with Language Selection

Teachers MUST be able to export exams to Moodle XML format by selecting a target language.

#### Field: Language Selection
- **TYPE:** CharField with choices
- **CHOICES:** Dynamic list of available languages from question content
- **DEFAULT:** 'en' if available, otherwise first available language
- **VALIDATION:** Selected language must exist in at least one question

#### URL Pattern
```python
path('exams/<uuid:pk>/export/', ExamMoodleExportView.as_view(), name='export')
```

#### Scenario: Export exam with English content
- **GIVEN** exam "Midterm 2026" with 3 pools containing questions in English and Portuguese
- **WHEN** teacher navigates to `/exams/<exam-id>/export/`
- **AND** selects language "English (en)"
- **AND** clicks "Download XML"
- **THEN** browser downloads `midterm-2026.xml` file
- **AND** file contains questions rendered in English
- **AND** file contains valid Moodle XML structure

#### Scenario: Export exam with missing language
- **GIVEN** exam "Final Exam" with questions only in Portuguese
- **WHEN** teacher selects language "French (fr)"
- **THEN** system uses language fallback logic (first available language)
- **AND** displays warning: "Some questions not available in French, using fallback"

### Requirement: Moodle XML Generation

The system MUST tag every exported question variant with the identifier of its
source `QuestionPool`. `QuestionPool.order` is a positive integer and the
Moodle tag MUST be formatted as `q{order}`. Exported question names MAY remain
globally sequential and unique.

The existing export URL remains
`/exams/<uuid:pk>/export/`, for example
`/exams/123e4567-e89b-12d3-a456-426614174000/export/`.
This change has no Bootstrap components, templates, static files, CSS, or
JavaScript and therefore requires no `{% compress %}` blocks.

#### Scenario: Multiple versions of question one share q1

- **GIVEN** question pool 1 contains one template configured for three versions
- **WHEN** the Moodle XML export is generated
- **THEN** all three exported questions contain the tag `q1`
- **AND** none of those variants is tagged `q2` or `q3`

#### Scenario: Multiple templates in one pool share the pool tag

- **GIVEN** question pool 1 contains multiple templates and versions
- **WHEN** the Moodle XML export is generated
- **THEN** every exported question produced by that pool contains the tag `q1`

#### Scenario: Later question pool uses its own tag

- **GIVEN** question pool 1 and question pool 2 both produce variants
- **WHEN** the Moodle XML export is generated
- **THEN** variants from pool 1 contain the tag `q1`
- **AND** variants from pool 2 contain the tag `q2`

### Requirement: Fraction Calculation

The system MUST calculate answer fractions based on grading mode and number of choices.

#### Function: `calculate_fractions(num_choices: int, grading_mode: str) -> dict`

Returns dictionary with:
- `'correct'`: Fraction for correct answer (order=0)
- `'wrong'`: Fraction for wrong answers

#### Single Choice Mode Logic

Formula: `wrong_fraction = -100 / (num_choices - 1)`

```python
if grading_mode == 'single':
    wrong_fraction = -100.0 / (num_choices - 1)
    return {
        'correct': Decimal('100.0'),
        'wrong': Decimal(str(wrong_fraction))
    }
```

Examples:
- 2 choices: correct=100%, wrong=-100%
- 3 choices: correct=100%, wrong=-50%
- 4 choices: correct=100%, wrong=-33.33%
- 5 choices: correct=100%, wrong=-25%
- 6 choices: correct=100%, wrong=-20%

#### Multi Choice Mode Logic (2-6 choices)
| Choices | Correct | Wrong | Rationale |
|---------|---------|-------|-----------|
| 2 | 90 | 10 | Max score: correct + 1 wrong = 100% |
| 3 | 80 | 10 | Max score: correct + 2 wrong = 100% |
| 4 | 70 | 10 | Max score: correct + 3 wrong = 100% |
| 5 | 60 | 10 | Max score: correct + 4 wrong = 100% |
| 6 | 75 | 5 | Max score: correct + 5 wrong = 100% |

#### Scenario: Calculate fractions for valid multi-choice
- **GIVEN** grading_mode="multi" and num_choices=4
- **WHEN** calculate_fractions(4, "multi") is called
- **THEN** returns `{'correct': 70, 'wrong': 10}`

#### Scenario: Calculate fractions for invalid choice count
- **GIVEN** grading_mode="multi" and num_choices=8
- **WHEN** calculate_fractions(8, "multi") is called
- **THEN** raises ValueError with message: "Multi-choice mode only supports 2-6 choices, got 8"

### Requirement: Markdown to HTML Conversion

The system MUST convert Markdown text to HTML suitable for placement in CDATA
sections by the Moodle XML serializer.

#### Function: `format_html_for_moodle(markdown_text: str) -> str`

Process:
1. Convert markdown to HTML using `markdown.markdown()`
2. Escape any `]]>` terminator in the rendered HTML
3. Return the HTML string

#### Markdown Features Support
- **Paragraphs:** `<p>` tags
- **Code blocks:** `<pre><code>` with proper escaping
- **Inline code:** `<code>` tags
- **Emphasis:** `<em>` and `<strong>`
- **Lists:** `<ul>` and `<ol>`
- **Line breaks:** `<br>` from nl2br extension

#### Scenario: Convert simple markdown with code
- **GIVEN** markdown text: "Use `<article>` tag"
- **WHEN** format_html_for_moodle() is called
- **THEN** returns: `<p>Use <code>&lt;article&gt;</code> tag</p>`

#### Scenario: Convert markdown with special characters
- **GIVEN** markdown text: `Code: <div id="test">`
- **WHEN** format_html_for_moodle() is called
- **THEN** HTML entities are preserved inside CDATA
- **AND** XML parser treats content as literal text

### Requirement: Language Selection and Fallback

The system MUST extract text content in the specified language using the
multilingual question fallback logic.

#### Function: `extract_language_text(json_field: dict, language: str) -> str`

Process:
1. Parse JSONField content for `==lang==` markers
2. Extract text for requested language
3. If not found, use fallback (first available language)
4. Return plain text string

#### Scenario: Extract text in requested language
- **GIVEN** question text: `{"content": "==en==What is HTML?==pt==O que é HTML?"}`
- **AND** requested language="en"
- **WHEN** extract_language_text() is called
- **THEN** returns: "What is HTML?"

#### Scenario: Extract with fallback
- **GIVEN** question text: `{"content": "==en==What is HTML?==pt==O que é HTML?"}`
- **AND** requested language="fr"
- **WHEN** extract_language_text() is called
- **THEN** returns: "What is HTML?" (first available)
- **AND** logs warning about fallback usage

### Requirement: Export Download Response

The system MUST serve generated XML files as downloadable responses with proper
headers.

#### HTTP Response Configuration
- **Content-Type:** `application/xml`
- **Content-Disposition:** `attachment; filename="{exam-slug}.xml"`
- **Charset:** `utf-8`
- **Filename format:** Slugified exam title with `.xml` extension

#### Scenario: Download XML file
- **GIVEN** exam title "Midterm Exam 2026"
- **WHEN** export download is triggered
- **THEN** response has Content-Type "application/xml"
- **AND** filename is "midterm-exam-2026.xml"
- **AND** browser prompts download (not display)

## UI Components

### Location
`apps/exams/templates/exams/`

### Template: exam_export.html

Bootstrap 5.3.8 form with:

```html
{% extends "common/base.html" %}

{% block content %}
<div class="container mt-4">
  <h1>Export Exam: {{ exam.title }}</h1>
  
  <form method="post" class="mt-4">
    {% csrf_token %}
    
    <div class="mb-3">
      <label for="id_language" class="form-label">Select Language</label>
      <select name="language" id="id_language" class="form-select" required>
        {% for code, name in available_languages %}
          <option value="{{ code }}">{{ name }}</option>
        {% endfor %}
      </select>
      <div class="form-text">
        Questions will be exported in this language (with fallback for missing translations)
      </div>
    </div>
    
    <div class="alert alert-info">
      <i class="fas fa-info-circle"></i>
      This export will generate <strong>{{ total_questions }}</strong> questions
      ({{ exam.pools.count }} pools × variants)
    </div>
    
    <div class="d-flex gap-2">
      <button type="submit" class="btn btn-primary">
        <i class="fas fa-download"></i> Download XML
      </button>
      <a href="{% url 'exams:detail' exam.pk %}" class="btn btn-secondary">
        Cancel
      </a>
    </div>
  </form>
</div>
{% endblock %}
```

### Modified Template: exam_detail.html

Add export button in header:

```html
<div class="d-flex justify-content-between align-items-center mb-4">
  <h1>{{ exam.title }}</h1>
  <div class="btn-group">
    <a href="{% url 'exams:update' exam.pk %}" class="btn btn-outline-primary">
      <i class="fas fa-edit"></i> Edit
    </a>
    <a href="{% url 'exams:export' exam.pk %}" class="btn btn-success">
      <i class="fas fa-file-export"></i> Export to Moodle
    </a>
    <a href="{% url 'exams:delete' exam.pk %}" class="btn btn-outline-danger">
      <i class="fas fa-trash"></i> Delete
    </a>
  </div>
</div>
```

### Modified Template: exam_form.html

Add grading mode field:

```html
<div class="mb-3">
  <label class="form-label">Grading Mode</label>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="grading_mode" 
           id="grading_single" value="single" 
           {% if form.grading_mode.value == 'single' %}checked{% endif %}>
    <label class="form-check-label" for="grading_single">
      <strong>Single Choice</strong> - Traditional mode (one correct answer, -33% penalty for wrong)
    </label>
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="grading_mode" 
           id="grading_multi" value="multi"
           {% if form.grading_mode.value == 'multi' %}checked{% endif %}>
    <label class="form-check-label" for="grading_multi">
      <strong>Multiple Choice</strong> - Excel tracking mode (custom fractions for answer pattern analysis)
    </label>
  </div>
</div>
```

## Implementation

### Location
`apps/exams/moodle_export.py`

### Main Export Function

```python
from decimal import Decimal
from typing import Dict, List, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import markdown

def generate_moodle_xml(exam: Exam, language: str) -> str:
    """
    Generate Moodle XML for an exam.
    
    Args:
        exam: Exam instance to export
        language: Target language code (e.g., 'en', 'pt')
    
    Returns:
        Pretty-printed XML string
        
    Raises:
        ValueError: If exam has multi-choice pools with >6 choices
    """
    root = Element('quiz')
    
    for pool in exam.pools.order_by('order'):
        for pool_template in pool.pool_templates.all():
            template = pool_template.template
            num_versions = pool_template.number_of_versions
            
            # Validate choice count for multi-choice mode
            choice_count = template.choices.count()
            if exam.grading_mode == 'multi' and choice_count > 6:
                raise ValueError(
                    f"Multi-choice mode only supports 2-6 choices. "
                    f"Pool {pool.order} template '{template.title}' has {choice_count} choices."
                )
            
            # Generate variants
            for version_num in range(num_versions):
                question_elem = create_question_element(
                    pool=pool,
                    template=template,
                    version=version_num,
                    language=language,
                    grading_mode=exam.grading_mode
                )
                root.append(question_elem)
    
    # Pretty print
    xml_str = tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ')
```

### Fraction Calculation

```python
def calculate_fractions(num_choices: int, grading_mode: str) -> Dict[str, int]:
    """
    Calculate answer fractions based on grading mode.
    
    Args:
        num_choices: Number of answer choices
        grading_mode: 'single' or 'multi'
        
    Returns:
        Dict with 'correct' and 'wrong' fraction values
        
    Raises:
        ValueError: If multi mode used with unsupported choice count
    """
    if grading_mode == 'single':
        return {'correct': 100, 'wrong': -33.33333}
    
    # Multi-choice mode
    fraction_map = {
        2: {'correct': 90, 'wrong': 10},
        3: {'correct': 80, 'wrong': 10},
        4: {'correct': 70, 'wrong': 10},
        5: {'correct': 60, 'wrong': 10},
        6: {'correct': 75, 'wrong': 5},
    }
    
    if num_choices not in fraction_map:
        raise ValueError(
            f"Multi-choice mode only supports 2-6 choices, got {num_choices}"
        )
    
    return fraction_map[num_choices]
```

## Testing

### Location
`apps/exams/tests.py`

### Test Coverage

```python
class MoodleExportTests(TestCase):
    """Tests for Moodle XML export functionality."""
    
    def test_calculate_fractions_single_mode(self):
        """Test fraction calculation for single-choice mode."""
        result = calculate_fractions(4, 'single')
        self.assertEqual(result['correct'], 100)
        self.assertEqual(result['wrong'], -33.33333)
    
    def test_calculate_fractions_multi_4_choices(self):
        """Test fraction calculation for 4-choice multi mode."""
        result = calculate_fractions(4, 'multi')
        self.assertEqual(result['correct'], 70)
        self.assertEqual(result['wrong'], 10)
    
    def test_calculate_fractions_multi_6_choices(self):
        """Test fraction calculation for 6-choice multi mode."""
        result = calculate_fractions(6, 'multi')
        self.assertEqual(result['correct'], 75)
        self.assertEqual(result['wrong'], 5)
    
    def test_calculate_fractions_invalid_choice_count(self):
        """Test error for unsupported choice count."""
        with self.assertRaises(ValueError) as ctx:
            calculate_fractions(8, 'multi')
        self.assertIn('2-6 choices', str(ctx.exception))
    
    def test_format_html_for_moodle_with_code(self):
        """Test markdown conversion with code blocks."""
        markdown_text = "Use `<article>` tag"
        result = format_html_for_moodle(markdown_text)
        self.assertIn('<code>', result)
        self.assertIn('</code>', result)

    def test_export_uses_real_cdata(self):
        """Test exported HTML is serialized in a genuine CDATA section."""
        xml = generate_moodle_xml(self.exam, 'en')
        self.assertIn('<![CDATA[', xml)
        self.assertNotIn('&lt;![CDATA[', xml)
    
    def test_export_view_returns_xml_file(self):
        """Test export view returns downloadable XML."""
        exam = Exam.objects.create(title="Test Exam", grading_mode="single")
        pool = QuestionPool.objects.create(exam=exam, order=1)
        
        response = self.client.post(
            reverse('exams:export', kwargs={'pk': exam.pk}),
            {'language': 'en'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xml', response['Content-Disposition'])
```

## Dependencies

- [exam-management](../../specs/exam-management/spec.md) - Exam and QuestionPool models
- [multilingual-questions](../../../specs/multilingual-questions/spec.md) - Language marker parsing
- [question-variant-generation](../question-variant-generation/spec.md) - Variable substitution

## Related Specifications

- [question-variant-generation](../question-variant-generation/spec.md) - How variants are generated
- [grading-mode-selection](../grading-mode-selection/spec.md) - UI for selecting grading mode
