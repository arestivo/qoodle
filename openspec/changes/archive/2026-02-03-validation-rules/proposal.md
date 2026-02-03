# Proposal: Validation Rules for Questions

**Status:** Draft  
**Created:** 2026-02-03  
**Owner:** TBD

## Problem Statement

When generating questions with variables, some combinations of generated values may be invalid or undesirable even though each individual variable is valid. For example:
- In geometry problems, three randomly generated side lengths may not form a valid triangle
- Mathematical operations may produce non-integer results when integers are required
- One variable may need to be greater than another (e.g., `a > b`)
- Complex domain-specific constraints that are too difficult to express during variable generation

Currently, there's no way to validate that the combination of generated variables meets specific criteria, leading to potentially invalid or meaningless questions.

## Proposed Solution

Add a `validation_rules` JSONField to the Question model that stores a list of Python expressions. These expressions are evaluated after variable generation, and if any rule fails, the variables are regenerated until all rules pass (up to a maximum number of attempts).

### Key Components

1. **Validation Rules Storage**
   - Add `validation_rules` JSONField to Question model
   - Store as list of string expressions (e.g., `["a > b", "a + b > c", "result % 1 == 0"]`)

2. **Rule Evaluation**
   - Evaluate rules after variables are generated
   - Use same context/namespace as variable expressions
   - Regenerate if any rule returns `False`
   - Maximum retry limit to prevent infinite loops

3. **UI Integration**
   - Add validation rules field to question form
   - Dynamic rule addition (similar to choices)
   - Clear help text with examples
   - Error messages when max retries exceeded

## Technical Design

### Database Changes

**Question Model (`apps/questions/models.py`)**

```python
validation_rules = models.JSONField(
    default=list,
    blank=True,
    help_text="List of validation expressions (e.g., ['a > b', 'a + b > c'])"
)
```

**Migration:** Create migration to add `validation_rules` field

### Rule Evaluation Logic

**Location:** `apps/questions/models.py` in Question model

```python
def generate_variables(self, max_validation_attempts: int = 100) -> dict:
    """
    Generate variables and validate against rules.
    
    Args:
        max_validation_attempts: Maximum attempts to generate valid variables
        
    Returns:
        dict: Generated variables that pass all validation rules
        
    Raises:
        ValidationError: If unable to generate valid variables within max attempts
    """
    for attempt in range(max_validation_attempts):
        variables = self._generate_variables_once()
        
        if self._validate_rules(variables):
            return variables
    
    raise ValidationError(
        f"Unable to generate valid variables after {max_validation_attempts} attempts. "
        "Validation rules may be too restrictive or incompatible with variable definitions."
    )

def _validate_rules(self, variables: dict) -> bool:
    """
    Check if generated variables pass all validation rules.
    
    Args:
        variables: Dictionary of generated variable values
        
    Returns:
        bool: True if all rules pass, False otherwise
    """
    if not self.validation_rules:
        return True
    
    # Create evaluation context with generated variables
    context = variables.copy()
    context['__builtins__'] = SAFE_BUILTINS
    
    for rule in self.validation_rules:
        try:
            result = eval(rule, context)
            if not result:
                return False
        except Exception:
            # If rule evaluation fails, treat as validation failure
            return False
    
    return True
```

### Form Changes

**QuestionForm (`apps/questions/forms.py`)**

- Add `validation_rules` field (similar to how variables are handled)
- Display as textarea or dynamic list with add/remove buttons
- Validate that rules are syntactically correct Python expressions
- Show helpful examples in help text

### Template Changes

**question_form.html**

Add validation rules section after variables:

```html
<div class="mb-3">
    <label for="id_validation_rules" class="form-label">
        Validation Rules
        <span class="text-muted">(Optional)</span>
    </label>
    <div id="validation-rules-container">
        <!-- Dynamic rule inputs -->
    </div>
    <button type="button" class="btn btn-sm btn-outline-primary" id="add-rule">
        <i class="fa-solid fa-plus"></i> Add Rule
    </button>
    <div class="form-text">
        Add Python expressions to validate generated variables.
        Examples: <code>a &gt; b</code>, <code>a + b &gt; c</code>, <code>result % 1 == 0</code>
    </div>
</div>
```

**question_preview.html**

Display validation rules in question metadata section.

### JavaScript Changes

**question_form.js**

Add rule management functions:
- `addValidationRule()` - Add new rule input
- `removeValidationRule(index)` - Remove rule input
- Serialize rules to hidden field on form submit

### Error Handling

When max attempts exceeded during preview/rendering:
- Display clear error message to user
- Suggest reviewing validation rules and variable definitions
- Show which rules are failing (if possible)
- Allow editing without regenerating

## Implementation Plan

### Phase 1: Database & Model (Day 1)
- [ ] Add `validation_rules` JSONField to Question model
- [ ] Create and run migration
- [ ] Add `_validate_rules()` method
- [ ] Modify `generate_variables()` to use validation with retry logic
- [ ] Update `_generate_variables_once()` (extract from current `generate_variables()`)
- [ ] Write unit tests for validation logic

### Phase 2: Form & Validation (Day 2)
- [ ] Add validation_rules field to QuestionForm
- [ ] Add form validation for rule syntax
- [ ] Handle JSON serialization/deserialization
- [ ] Write tests for form handling
- [ ] Update admin interface to show validation rules

### Phase 3: UI & JavaScript (Day 3)
- [ ] Create validation rules section in question_form.html
- [ ] Implement JavaScript for dynamic rule management
- [ ] Add HTML template for rule inputs
- [ ] Style rule inputs consistently with rest of form
- [ ] Add help text and examples

### Phase 4: Preview & Error Handling (Day 4)
- [ ] Update QuestionPreviewView to handle validation errors
- [ ] Add error messages for max retry exceeded
- [ ] Display validation rules in preview template
- [ ] Test error scenarios and edge cases

### Phase 5: Testing & Documentation (Day 5)
- [ ] Write comprehensive unit tests (model methods, validation logic)
- [ ] Write integration tests (form submission, preview generation)
- [ ] Test edge cases (no rules, invalid rules, impossible rules)
- [ ] Manual browser testing
- [ ] Update documentation
- [ ] Code quality checks (black, ruff, mypy)

## Testing Strategy

### Unit Tests

**Model Tests (`apps/questions/tests.py`)**
- `test_validate_rules_all_pass` - All rules return True
- `test_validate_rules_one_fails` - One rule returns False
- `test_validate_rules_empty` - No rules always passes
- `test_validate_rules_syntax_error` - Invalid rule syntax
- `test_generate_variables_with_validation` - Successful generation with rules
- `test_generate_variables_max_retries` - Raises error after max attempts
- `test_validation_rule_with_undefined_variable` - Rule references undefined variable
- `test_complex_validation_rules` - Triangle inequality, integer results, etc.

**Form Tests**
- `test_validation_rules_field_valid_input` - Valid rules accepted
- `test_validation_rules_field_invalid_syntax` - Invalid syntax rejected
- `test_validation_rules_serialization` - JSON encoding/decoding

### Integration Tests
- `test_question_create_with_validation_rules` - Create question with rules via form
- `test_question_preview_with_validation_rules` - Preview respects rules
- `test_question_preview_validation_error` - Shows error when rules can't be satisfied

### Manual Testing
- Create question with simple rule (`a > b`)
- Create question with complex rule (triangle inequality: `a + b > c and b + c > a and c + a > b`)
- Create question with impossible rule (`a > 10 and a < 5`)
- Verify max retries error message
- Test rule add/remove UI interactions

## Dependencies

- **Required:** Variable system (already implemented in question-variables change)
- **Related:** Uses same safe evaluation context as expression variables
- **No breaking changes:** Existing questions without rules continue to work

## Risks & Considerations

### Security
- **Eval risk:** Reuse `SAFE_BUILTINS` from variable system to prevent code injection
- **Input validation:** Validate rule syntax before saving

### Performance
- **Regeneration cost:** Complex rules may require many regeneration attempts
  - Mitigation: Hardcoded max attempts (100) prevents infinite loops
  - Future: Could be configurable per question if needed
- **Preview rendering:** May be slower for questions with restrictive rules
  - Mitigation: Clearly communicate to users via error messages

### Usability
- **User education:** Users need to understand Python expression syntax
  - Mitigation: Provide clear examples and help text
  - Mitigation: Show syntax errors immediately
- **Debugging:** Hard to know why rules are failing during generation
  - Future enhancement: Could show validation results in debug mode

### Data Integrity
- **Backward compatibility:** Questions without `validation_rules` default to empty list
- **Migration:** Simple additive change, no data transformation needed

## Success Criteria

- [ ] Questions can have zero or more validation rules
- [ ] Rules are evaluated after variable generation
- [ ] Failed validation triggers regeneration (up to max attempts)
- [ ] Clear error message when max attempts exceeded
- [ ] UI allows easy addition/removal of rules
- [ ] All existing tests continue to pass
- [ ] New functionality has >80% test coverage
- [ ] Documentation includes examples of common validation patterns
- [ ] Example questions demonstrating:
  - Triangle inequality validation
  - Integer result validation
  - Comparative validation (a > b)
  - Range validation
