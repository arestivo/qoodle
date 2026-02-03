# variable-system Specification (Delta)

## ADDED Requirements

### Requirement: Validation Rules for Variable Constraints

Questions SHALL support validation rules that constrain randomly generated variables to satisfy specific conditions, with automatic retry logic until valid values are found.

#### Scenario: Simple comparison validation rule
- **GIVEN** a question has variables `a` and `b` defined as numbers (1-10)
- **WHEN** a validation rule "a > b" is defined
- **THEN** variable generation retries until `a` is greater than `b`
- **AND** the generated question always has `a > b`

#### Scenario: Multiple validation rules (triangle inequality)
- **GIVEN** a question has variables `a`, `b`, `c` defined as numbers (1-20)
- **WHEN** validation rules ["a + b > c", "b + c > a", "a + c > b"] are defined
- **THEN** variable generation retries until all three inequalities hold
- **AND** the generated values form a valid triangle

#### Scenario: Validation rule for integer results
- **GIVEN** a question has variables `a` and `b` defined as numbers
- **WHEN** a validation rule "(a + b) % 1 == 0" is defined
- **THEN** variable generation retries until the sum is an integer
- **AND** expressions like "{{a + b}}" render without decimal places

#### Scenario: Impossible validation rules
- **GIVEN** a question has variable `x` defined as number (1-5)
- **WHEN** validation rules ["x > 10", "x < 3"] are defined (impossible)
- **THEN** variable generation fails after 100 retry attempts
- **AND** a ValidationError is raised with helpful message
- **AND** the preview UI shows clear error message with suggestions

#### Scenario: Validation rules in form submission
- **GIVEN** a teacher is creating/editing a question
- **WHEN** they add validation rules via the UI
- **THEN** rules are validated for syntax errors before saving
- **AND** invalid Python syntax shows form validation error
- **AND** valid rules are stored as JSON array in database

---

### Requirement: Validation Rule Syntax Checking

Validation rules MUST be checked for Python syntax errors during form submission to prevent runtime errors.

#### Scenario: Valid Python expression accepted
- **GIVEN** a teacher is adding a validation rule
- **WHEN** they enter "a > b and b > 0"
- **THEN** the form validates successfully
- **AND** the rule is saved to the database

#### Scenario: Invalid Python syntax rejected
- **GIVEN** a teacher is adding a validation rule
- **WHEN** they enter "a >> b" (invalid comparison)
- **THEN** the form shows validation error
- **AND** the error message indicates syntax problem
- **AND** the question is not saved until corrected

#### Scenario: Undefined variable in rule
- **GIVEN** a question has only variable `a` defined
- **WHEN** a validation rule "a > b" is added (b undefined)
- **THEN** the form accepts it (checked at generation time)
- **AND** variable generation raises clear error about undefined `b`

---

### Requirement: UI for Managing Validation Rules

The question form MUST provide dynamic UI for adding, editing, and removing validation rules with examples and help text.

#### Scenario: Add validation rule via UI
- **GIVEN** a teacher is editing a question
- **WHEN** they click "Add Rule" button
- **THEN** a new rule input field appears
- **AND** they can enter a Python expression
- **AND** examples are shown: "a > b", "a + b > c", "result % 1 == 0"

#### Scenario: Remove validation rule via UI
- **GIVEN** a question has 3 validation rules
- **WHEN** the teacher clicks delete button on the 2nd rule
- **THEN** the rule is removed from the list
- **AND** remaining rules maintain their order
- **AND** the form can be saved without that rule

#### Scenario: Edit existing validation rules
- **GIVEN** a question has validation rules saved
- **WHEN** the teacher opens the edit form
- **THEN** all existing rules are displayed in input fields
- **AND** each can be modified or deleted
- **AND** new rules can be added

---

### Requirement: Error Handling for Validation Failures

The system MUST provide clear, actionable error messages when validation rules cannot be satisfied during preview or quiz generation.

#### Scenario: Preview shows validation error
- **GIVEN** a question has impossible validation rules
- **WHEN** a teacher views the preview
- **THEN** an error message is displayed instead of question
- **AND** the message shows which rules were defined
- **AND** suggestions are provided (review rules, check variable ranges)
- **AND** a link to edit the question is shown

#### Scenario: Maximum retry attempts exceeded
- **GIVEN** a question has validation rules
- **WHEN** 100 generation attempts all fail validation
- **THEN** a ValidationError is raised
- **AND** the error message indicates max attempts reached
- **AND** the preview UI catches this and shows user-friendly message

#### Scenario: Validation succeeds after retries
- **GIVEN** a question has validation rule "a > b"
- **WHEN** variables are generated with a=3, b=5 (fails)
- **THEN** generation retries with new random values
- **AND** continues until a > b is satisfied
- **AND** the valid values are used for rendering
- **AND** no error is shown to the user

---

## MODIFIED Requirements

### Requirement: Variable Generation with Seed

Questions SHALL generate deterministic random variables using a seed, **with validation rule checking and retry logic**.

#### Scenario: Generate variables with validation rules (MODIFIED)
- **GIVEN** a question has variables defined with validation rules
- **WHEN** `generate_variables(seed=42)` is called
- **THEN** variables are generated using the seed
- **AND** validation rules are checked
- **AND** if validation fails, new values are generated
- **AND** the process repeats up to max_validation_attempts (default 100)
- **AND** returns variables only when all rules pass

#### Scenario: Same seed with validation produces consistent results (ADDED)
- **GIVEN** a question has validation rules
- **WHEN** `generate_variables(seed=42)` is called multiple times
- **THEN** the same variable values are returned each time
- **AND** the same retry sequence occurs (deterministic randomness)

---
