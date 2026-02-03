# Tasks: Validation Rules for Questions

## Phase 1: Database & Model

### P1.1: Add validation_rules field to Question model
- [x] Add `validation_rules` JSONField to Question model in `apps/questions/models.py`
- [x] Set `default=list`, `blank=True`
- [x] Add appropriate help_text

### P1.2: Create migration
- [x] Run `poetry run python manage.py makemigrations questions`
- [x] Review generated migration
- [x] Run `poetry run python manage.py migrate`

### P1.3: Implement _validate_rules() method
- [x] Add `_validate_rules(variables: dict) -> bool` method to Question model
- [x] Check if `validation_rules` is empty (return True if no rules)
- [x] Create evaluation context with variables and SAFE_BUILTINS
- [x] Loop through each rule and eval it
- [x] Return False if any rule fails or raises exception
- [x] Return True if all rules pass

### P1.4: Refactor generate_variables() to extract _generate_variables_once()
- [x] Create `_generate_variables_once()` method with current generation logic
- [x] Keep all existing variable generation code in this method
- [x] Ensure it returns dict of generated variables

### P1.5: Update generate_variables() with validation retry logic
- [x] Modify `generate_variables()` to accept `max_validation_attempts` parameter (default 100)
- [x] Implement retry loop: for attempt in range(max_validation_attempts)
- [x] Call `_generate_variables_once()` in each iteration
- [x] Call `_validate_rules(variables)` to check if valid
- [x] Return variables if validation passes
- [x] Raise ValidationError if max attempts exceeded with helpful message

### P1.6: Write model unit tests
- [x] Test `test_validate_rules_all_pass` - all rules return True
- [x] Test `test_validate_rules_one_fails` - one rule returns False
- [x] Test `test_validate_rules_empty` - no rules always passes
- [x] Test `test_validate_rules_syntax_error` - invalid rule syntax handled
- [x] Test `test_generate_variables_with_validation` - successful generation with rules
- [x] Test `test_generate_variables_max_retries` - raises ValidationError after max attempts
- [x] Test `test_validation_rule_undefined_variable` - rule references undefined variable
- [x] Test `test_complex_validation_rules` - triangle inequality, integer results

## Phase 2: Form & Validation

### P2.1: Add validation_rules to QuestionForm
- [ ] Add `validation_rules` field to QuestionForm in `apps/questions/forms.py`
- [ ] Use JSONField or CharField with JSON handling
- [ ] Add widget configuration for textarea display
- [ ] Add help_text with examples

### P2.2: Implement form validation for rules
- [ ] Add `clean_validation_rules()` method to QuestionForm
- [ ] Parse rules as JSON list if string input
- [ ] Validate each rule is a string
- [ ] Test syntax by attempting compile() on each rule
- [ ] Return cleaned list of rules

### P2.3: Handle JSON serialization in form save
- [ ] Ensure validation_rules saves as list to JSONField
- [ ] Handle both string and list input formats
- [ ] Test round-trip: save and reload

### P2.4: Update admin interface
- [ ] Add `validation_rules` to QuestionAdmin fieldsets
- [ ] Place in appropriate section (e.g., "Variables and Validation")
- [ ] Test admin UI display and editing

### P2.5: Write form tests
- [ ] Test `test_validation_rules_field_valid_input` - valid rules accepted
- [ ] Test `test_validation_rules_field_invalid_syntax` - invalid syntax rejected
- [ ] Test `test_validation_rules_serialization` - JSON encoding/decoding works
- [ ] Test `test_validation_rules_empty` - empty list handled correctly

## Phase 3: UI & JavaScript

### P3.1: Create validation rules section in question_form.html
- [ ] Add validation rules section after variables section
- [ ] Include label "Validation Rules (Optional)"
- [ ] Add container div for dynamic rules
- [ ] Add "Add Rule" button
- [ ] Add help text with examples

### P3.2: Create HTML template for rule inputs
- [ ] Create `<template>` element for rule input row
- [ ] Include text input for rule expression
- [ ] Include delete button for each rule
- [ ] Add appropriate styling classes

### P3.3: Implement JavaScript for rule management
- [ ] Add `addValidationRule()` function in `question_form.js`
- [ ] Add `removeValidationRule(index)` function
- [ ] Add event listener for "Add Rule" button
- [ ] Add event listeners for delete buttons
- [ ] Implement rule numbering/indexing

### P3.4: Implement form serialization
- [ ] Collect all rule inputs on form submit
- [ ] Serialize to JSON array
- [ ] Store in hidden field or textarea for form submission
- [ ] Handle empty rules list

### P3.5: Add client-side validation hints
- [ ] Add basic syntax checking on blur/change
- [ ] Show visual feedback for common errors
- [ ] Keep validation non-blocking (server validates authoritatively)

## Phase 4: Preview & Error Handling ✅

### P4.1: Update question_preview.html to display rules ✅
- [x] Add validation rules section to preview template
- [x] Display rules as list if present
- [x] Show "No validation rules" if empty
- [x] Format rules with code styling

### P4.2: Handle validation errors in QuestionPreviewView ✅
- [x] Wrap question rendering in try/except for ValidationError
- [x] Catch validation retry limit errors
- [x] Render error template with helpful message
- [x] Suggest reviewing rules and variables

### P4.3: Create error message template ✅
- [x] Design user-friendly error message
- [x] Include: number of attempts made, suggestion to review rules
- [x] Add link back to edit question
- [x] Show which rules failed (if traceable)

### P4.4: Test error scenarios ✅
- [x] Test impossible rules (a > 10 and a < 5)
- [x] Test rules with undefined variables
- [x] Test conflicting rules
- [x] Verify error messages are clear and helpful

## Phase 5: Testing & Documentation

### P5.1: Write comprehensive integration tests
- [ ] Test `test_question_create_with_validation_rules` - create via form
- [ ] Test `test_question_update_with_validation_rules` - update existing
- [ ] Test `test_question_preview_with_validation_rules` - preview respects rules
- [ ] Test `test_question_preview_validation_error` - error shown when rules fail

### P5.2: Manual browser testing
- [ ] Create question with simple rule (a > b)
- [ ] Create question with triangle inequality rule
- [ ] Create question with impossible rule
- [ ] Test add/remove rule UI
- [ ] Test form validation and error messages
- [ ] Test preview with valid and invalid rule combinations

### P5.3: Test edge cases
- [ ] Question with no variables but has rules
- [ ] Question with variables but no rules
- [ ] Empty rule strings
- [ ] Very long rule expressions
- [ ] Rules with special characters
- [ ] Multiple rules with same condition

### P5.4: Run code quality checks
- [ ] Run `poetry run black apps/questions/`
- [ ] Run `poetry run ruff check apps/questions/`
- [ ] Fix any style issues
- [ ] Verify mypy type hints (if applicable)

### P5.5: Verify test coverage
- [ ] Run pytest with coverage
- [ ] Ensure >80% coverage for new code
- [ ] Add tests for any uncovered branches

### P5.6: Ensure all existing tests pass
- [ ] Run full test suite: `poetry run pytest`
- [ ] Fix any regressions
- [ ] Verify backward compatibility

### P5.7: Create example questions
- [ ] Example 1: Triangle inequality validation
- [ ] Example 2: Integer result validation
- [ ] Example 3: Comparative validation (a > b)
- [ ] Example 4: Range validation
- [ ] Document examples in tests or fixtures
