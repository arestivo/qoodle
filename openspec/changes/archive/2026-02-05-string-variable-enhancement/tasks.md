# Tasks: String Variable Enhancement

## Phase 0: Update Form UI

- [x] Update HTML template to use `values` input instead of `min_length`/`max_length`
- [x] Update JavaScript serialization to use `values` array
- [x] Update JavaScript deserialization to load `values` array

## Phase 1: Update Generator

- [x] Modify `VariableGenerator.generate_string()` to accept `values` list parameter
- [x] Use `random.choice(values)` to select a single value
- [x] Remove `min_length` and `max_length` parameters

## Phase 2: Update Validation

- [x] Update `_validate_variable_definition()` for string type:
  - Require `values` field
  - Validate `values` is a non-empty list
- [x] Remove validation for `min_length` and `max_length`

## Phase 3: Update Model Documentation

- [x] Update `QuestionTemplate` docstring to reflect new string variable format
- [x] Update example in docstring

## Phase 4: Testing

- [x] Test string variable generation with multiple values
- [x] Test string variable generation with single value
- [x] Test validation rejects missing `values` field
- [x] Test validation rejects empty `values` list
- [x] Test seed reproducibility
