# variable-system Specification

## Purpose
TBD - created by archiving change question-variables. Update Purpose after archive.
## Requirements
### Requirement: Variable Definition Storage

Questions SHALL be able to define multiple variables of different types, stored as structured data that can be validated and evaluated.

#### Scenario: Define numeric variable with constraints
- **GIVEN** a teacher is creating a question
- **WHEN** they define a variable `a` as type `num` with min=1, max=10, precision=0.1
- **THEN** the variable definition is stored in the Question's `variables` JSONField
- **AND** the variable can generate random values like 1.0, 5.3, 9.7

#### Scenario: Define string variable with length constraints
- **GIVEN** a teacher is creating a question
- **WHEN** they define a variable `word` as type `string` with min_length=3, max_length=8
- **THEN** the variable definition is stored in the Question's `variables` JSONField
- **AND** the variable can generate random strings of length 3-8 characters

#### Scenario: Define set variable with item selection
- **GIVEN** a teacher is creating a question  
- **WHEN** they define a variable `fruits` as type `set` with items=["apple", "banana", "cherry"] and size=2
- **THEN** the variable definition is stored in the Question's `variables` JSONField
- **AND** the variable can generate random 2-item subsets like ["apple", "cherry"]

#### Scenario: Define expression variable dependent on others
- **GIVEN** a teacher has defined variables `a` and `b` as numeric
- **WHEN** they define a variable `sum` as type `expression` with formula="a + b"
- **THEN** the variable definition is stored in the Question's `variables` JSONField
- **AND** the variable evaluates the expression using other variable values

---
### Requirement: Variable Substitution in Text

Question and choice text MUST support `{{variable}}` delimiter syntax for
variable substitution with expression evaluation. Choice text MUST additionally
evaluate complete `$expression$` segments against the supplied variable
context. Dollar-delimited evaluation MUST use the same restricted evaluator as
other variable expressions and MUST occur after `{{...}}` substitution.

`QuestionTemplate.text` and `Choice.text` remain multilingual JSONFields; no
field constraints change. This is model rendering behavior and introduces no
URL, Bootstrap component, template, static asset, or `{% compress %}` change.

#### Scenario: Simple variable substitution in question text

- **GIVEN** a question has variable `a=5` defined
- **WHEN** the question text is "What is {{a}} + 2?"
- **THEN** the rendered text is "What is 5 + 2?"

#### Scenario: Expression evaluation in question text

- **GIVEN** a question has variables `a=3` and `b=4` defined
- **WHEN** the question text is "The sum of {{a}} and {{b}} is {{a + b}}"
- **THEN** the rendered text is "The sum of 3 and 4 is 7"

#### Scenario: Variable substitution in choice text

- **GIVEN** a question has variable `answer=42` defined
- **WHEN** a choice text is "The answer is {{answer}}"
- **THEN** the rendered choice text is "The answer is 42"

#### Scenario: Complex expression in choice text

- **GIVEN** a question has variables `x=10` and `y=3` defined
- **WHEN** a choice text is "Result: {{(x / y) * 2}}"
- **THEN** the rendered choice text is "Result: 6.666666666666667" (or rounded appropriately)

#### Scenario: Multiple variables in same text

- **GIVEN** a question has variables `name="Alice"` and `age=25`
- **WHEN** the question text is "{{name}} is {{age}} years old"
- **THEN** the rendered text is "Alice is 25 years old"

#### Scenario: Entire choice is a dollar expression

- **GIVEN** generated variables `x=5` and `y=3`
- **AND** a choice text `$x + y$`
- **WHEN** `Choice.get_text(variables={"x": 5, "y": 3})` is called
- **THEN** the rendered choice text is `8`

#### Scenario: Dollar expression is embedded in choice text

- **GIVEN** generated variables `x=5` and `y=3`
- **AND** a choice text `Result: $x * y$ units`
- **WHEN** the choice is rendered
- **THEN** the rendered choice text is `Result: 15 units`

#### Scenario: Set item access in dollar expression

- **GIVEN** generated variable `items=["Paris, France", "London"]`
- **AND** a choice text `$items[0]$`
- **WHEN** the choice is rendered
- **THEN** the rendered choice text is `Paris, France`

#### Scenario: Normal substitution precedes dollar evaluation

- **GIVEN** generated variables `x=4` and `y=2`
- **AND** a choice text `$int("{{x}}") / y$`
- **WHEN** the choice is rendered
- **THEN** `{{x}}` is substituted before the dollar expression is evaluated
- **AND** the rendered choice text is `2.0`

#### Scenario: Multiple dollar expressions

- **GIVEN** generated variables `x=4` and `y=2`
- **AND** a choice text `$x + y$ and $x - y$`
- **WHEN** the choice is rendered
- **THEN** the rendered choice text is `6 and 2`

#### Scenario: Invalid expression remains literal

- **GIVEN** a choice text `$missing + 1$`
- **AND** the supplied variables do not define `missing`
- **WHEN** the choice is rendered
- **THEN** the text remains `$missing + 1$`

#### Scenario: Unmatched dollar remains literal

- **GIVEN** a choice text `Price is $5`
- **WHEN** the choice is rendered
- **THEN** the text remains `Price is $5`

#### Scenario: Question text does not use dollar evaluation

- **GIVEN** question text `$x + y$`
- **AND** generated variables `x=5` and `y=3`
- **WHEN** the question text is rendered
- **THEN** the question text remains `$x + y$`

### Requirement: Variable Type Validation

Each variable type MUST enforce its specific constraints during definition and generation.

#### Scenario: Numeric variable respects min/max bounds
- **GIVEN** a numeric variable defined with min=5, max=10
- **WHEN** the variable generates 100 random values
- **THEN** all values are >= 5 and <= 10

#### Scenario: Numeric variable respects precision
- **GIVEN** a numeric variable defined with precision=0.5
- **WHEN** the variable generates a value
- **THEN** the value is a multiple of 0.5 (e.g., 5.0, 5.5, 6.0)

#### Scenario: String variable enforces length constraints
- **GIVEN** a string variable defined with min_length=2, max_length=5
- **WHEN** the variable generates 100 random strings
- **THEN** all strings have length >= 2 and <= 5

#### Scenario: Set variable respects subset size
- **GIVEN** a set variable with items=["a", "b", "c", "d"] and size=2
- **WHEN** the variable generates a value
- **THEN** the result contains exactly 2 distinct items from the set

#### Scenario: Set variable size cannot exceed available items
- **GIVEN** a set variable with items=["a", "b", "c"]
- **WHEN** defining size=5 (larger than 3 items)
- **THEN** validation fails with error "Size cannot exceed number of items"

---

### Requirement: Expression Variable Evaluation

Expression variables MUST evaluate Python expressions in the context of other defined variables.

#### Scenario: Expression evaluates with numeric variables
- **GIVEN** variables `a=5` and `b=3` are defined
- **WHEN** expression variable `result` has formula="a + b * 2"
- **THEN** the expression evaluates to 11

#### Scenario: Expression uses Python built-in functions
- **GIVEN** variable `x=16` is defined
- **WHEN** expression variable `root` has formula="x ** 0.5"
- **THEN** the expression evaluates to 4.0

#### Scenario: Expression accesses string variables
- **GIVEN** variables `first="Hello"` and `last="World"`
- **WHEN** expression variable `greeting` has formula='f"{first} {last}!"'
- **THEN** the expression evaluates to "Hello World!"

#### Scenario: Expression with invalid syntax
- **GIVEN** no variables are defined
- **WHEN** expression variable has formula="a ++ b"
- **THEN** validation fails with SyntaxError during save

#### Scenario: Expression references undefined variable
- **GIVEN** only variable `a=5` is defined
- **WHEN** expression variable has formula="a + b"
- **THEN** validation fails with "Variable 'b' is not defined"

---

### Requirement: Circular Dependency Detection

The system MUST detect and prevent circular dependencies in expression variables.

#### Scenario: Direct circular dependency
- **GIVEN** expression variable `a` has formula="b"
- **WHEN** expression variable `b` has formula="a"
- **THEN** validation fails with "Circular dependency detected: a → b → a"

#### Scenario: Indirect circular dependency
- **GIVEN** expression variable `a` has formula="b"
- **AND** expression variable `b` has formula="c"
- **WHEN** expression variable `c` has formula="a"
- **THEN** validation fails with "Circular dependency detected: a → b → c → a"

#### Scenario: Self-reference
- **GIVEN** defining an expression variable `x`
- **WHEN** the formula is "x + 1"
- **THEN** validation fails with "Variable 'x' cannot reference itself"

#### Scenario: Valid dependency chain
- **GIVEN** numeric variables `a=2` and `b=3`
- **AND** expression variable `sum` has formula="a + b"
- **WHEN** expression variable `double` has formula="sum * 2"
- **THEN** validation succeeds and `double` evaluates to 10

---

### Requirement: Text Reference Validation

Question and choice text MUST only reference defined variables, and all references MUST be validated.

#### Scenario: Valid variable reference
- **GIVEN** question has variable `answer` defined
- **WHEN** question text is "The answer is {{answer}}"
- **THEN** validation succeeds

#### Scenario: Undefined variable reference in question
- **GIVEN** question has variable `a` defined but not `b`
- **WHEN** question text is "Values: {{a}} and {{b}}"
- **THEN** validation fails with "Undefined variable 'b' referenced in text"

#### Scenario: Undefined variable reference in choice
- **GIVEN** question has variable `x` defined but not `y`
- **WHEN** choice text is "Result: {{y}}"
- **THEN** validation fails with "Undefined variable 'y' referenced in choice text"

#### Scenario: Empty variable reference
- **GIVEN** question has variables defined
- **WHEN** question text contains "{{}}"
- **THEN** validation fails with "Empty variable reference"

#### Scenario: All references valid across multilingual text
- **GIVEN** question has variable `num` defined
- **AND** question text is `{"en": "Number {{num}}", "pt": "Número {{num}}"}`
- **THEN** validation succeeds for all languages

---

### Requirement: Variable Generation Determinism

Variable generation SHALL support seeding for reproducible results during testing and preview, **with validation rule checking and retry logic**.

#### Scenario: Generate variables with seed
- **GIVEN** a question with numeric variable `a` (min=1, max=100)
- **WHEN** generating variables with seed=42
- **THEN** the same seed produces the same value on multiple generations

#### Scenario: Generate variables without seed
- **GIVEN** a question with numeric variable `a` (min=1, max=100)
- **WHEN** generating variables without a seed
- **THEN** each generation produces different random values

#### Scenario: Preview shows multiple instances
- **GIVEN** a question with variables defined
- **WHEN** viewing the question preview
- **THEN** the UI shows 3-5 different random instances of the question

#### Scenario: Generate variables with validation rules
- **GIVEN** a question has variables defined with validation rules
- **WHEN** `generate_variables(seed=42)` is called
- **THEN** variables are generated using the seed
- **AND** validation rules are checked
- **AND** if validation fails, new values are generated
- **AND** the process repeats up to max_validation_attempts (default 100)
- **AND** returns variables only when all rules pass

#### Scenario: Same seed with validation produces consistent results
- **GIVEN** a question has validation rules
- **WHEN** `generate_variables(seed=42)` is called multiple times
- **THEN** the same variable values are returned each time
- **AND** the same retry sequence occurs (deterministic randomness)

---

### Requirement: Multilingual Integration

Variable substitution MUST work correctly with the existing multilingual text system.

#### Scenario: Variables in language-specific text
- **GIVEN** question has variable `x=5`
- **AND** multilingual text: `{"en": "Value is {{x}}", "pt": "Valor é {{x}}"}`
- **WHEN** rendering in English
- **THEN** text is "Value is 5"
- **AND** when rendering in Portuguese text is "Valor é 5"

#### Scenario: Variables in language-independent text
- **GIVEN** question has variable `formula="E=mc²"`
- **AND** text is `{"none": "{{formula}}"}`
- **WHEN** rendering in any language
- **THEN** text is "E=mc²"

#### Scenario: Variable substitution happens after language fallback
- **GIVEN** question has variable `n=10`
- **AND** multilingual text: `{"en": "Number {{n}}"}`
- **WHEN** rendering in Portuguese (not defined)
- **THEN** fallback to English occurs first
- **AND** then variable substitution produces "Number 10"

---

### Requirement: Form UI for Variable Definition

The question create and edit form MUST provide type-specific fields for each
variable type. For a set variable, items MUST be entered one per line in a
Bootstrap 5.3.8 `textarea.form-control.form-control-sm.var-items`. Each
non-empty trimmed line MUST become one string in the set variable's `items`
array, and commas inside a line MUST remain part of that item.

The form remains available at `GET` and `POST /questions/create/` and
`GET` and `POST /questions/<uuid:pk>/edit/`, for example
`/questions/123e4567-e89b-12d3-a456-426614174000/edit/`.
No model fields change: `QuestionTemplate.variables` remains a JSONField and
set definitions retain `{"type": "set", "items": list[str], "size": int}`.

The existing deferred
`apps/questions/static/questions/js/question_form.js` script MUST remain in the
`extra_js` block inherited from `common/base.html`, where it is already enclosed
by `{% compress js %}`.

#### Scenario: Set item contains a comma

- **GIVEN** a teacher is editing a set variable
- **WHEN** the items textarea contains:

  ```text
  Paris, France
  Porto, Portugal
  London
  ```

- **THEN** the serialized `items` value is
  `["Paris, France", "Porto, Portugal", "London"]`
- **AND** no item is split at a comma

#### Scenario: Blank lines and surrounding whitespace

- **GIVEN** a set items textarea contains blank lines and surrounding whitespace
- **WHEN** the variable definition is serialized
- **THEN** surrounding whitespace is removed from each item
- **AND** blank lines do not create empty items

#### Scenario: Existing set variable is loaded for editing

- **GIVEN** a saved set variable has
  `items = ["Paris, France", "Porto, Portugal"]`
- **WHEN** the question edit form is loaded
- **THEN** the textarea displays `Paris, France` and `Porto, Portugal` on separate lines
- **AND** saving without edits preserves both complete items

#### Scenario: Set generation preserves item punctuation

- **GIVEN** a set variable stores an item `"Paris, France"`
- **WHEN** the variable generator selects that item
- **THEN** the generated value is exactly `"Paris, France"`

### Requirement: Variable Preview and Testing

Teachers MUST be able to preview how questions render with different variable values.

#### Scenario: Preview shows random instances
- **GIVEN** a question with variables `a` and `b` (numeric, 1-10)
- **WHEN** viewing the preview page
- **THEN** at least 3 different random instances are displayed
- **AND** each shows different values for `a` and `b`

#### Scenario: Preview evaluates expressions correctly
- **GIVEN** question text "What is {{a}} + {{b}}? Answer: {{a+b}}"
- **AND** one instance has a=3, b=5
- **WHEN** viewing that instance
- **THEN** text displays "What is 3 + 5? Answer: 8"

#### Scenario: Preview shows all choices with variables
- **GIVEN** choices with text ["{{answer}}", "{{answer + 1}}", "{{answer - 1}}"]
- **AND** variable `answer=10`
- **WHEN** viewing preview
- **THEN** choices display as ["10", "11", "9"]

#### Scenario: Refresh preview generates new instances
- **GIVEN** viewing question preview
- **WHEN** teacher clicks "Refresh" button
- **THEN** new random variable values are generated
- **AND** question re-renders with new values

---

### Requirement: Error Handling and User Feedback

The system MUST provide clear, actionable error messages for variable-related issues.

#### Scenario: Display validation errors on save
- **GIVEN** a question with undefined variable reference in text
- **WHEN** teacher attempts to save the question
- **THEN** save is prevented
- **AND** error message shows "Question text references undefined variable 'x'"

#### Scenario: Show expression evaluation errors
- **GIVEN** expression variable with formula="1/0"
- **WHEN** evaluating the expression
- **THEN** error message shows "Division by zero in expression for variable 'x'"

#### Scenario: Highlight invalid variable definitions
- **GIVEN** numeric variable with min=10, max=5 (min > max)
- **WHEN** validation runs
- **THEN** error message shows "Variable 'x': min value cannot be greater than max value"

#### Scenario: Warning for unused variables
- **GIVEN** question has variable `unused` defined
- **WHEN** the variable is not referenced in any text
- **THEN** warning message shows "Variable 'unused' is defined but not used"

---

### Requirement: Database Schema Changes

The Question model MUST be extended to store variable definitions efficiently.

#### Scenario: Store variable definitions in JSONField
- **GIVEN** a Question model instance
- **WHEN** saving variable definitions
- **THEN** variables are stored in `variables` JSONField as:
```json
{
  "a": {
    "type": "num",
    "min": 1,
    "max": 10,
    "precision": 0.1
  },
  "name": {
    "type": "string",
    "min_length": 3,
    "max_length": 10
  },
  "items": {
    "type": "set",
    "items": ["red", "blue", "green"],
    "size": 2
  },
  "result": {
    "type": "expression",
    "formula": "a * 2"
  }
}
```

#### Scenario: Null or empty variables field is valid
- **GIVEN** a Question model instance
- **WHEN** the `variables` field is null or {}
- **THEN** the question is valid
- **AND** no variable substitution occurs during rendering

---

### Requirement: Backward Compatibility

Existing questions without variables MUST continue to work without modification.

#### Scenario: Existing question without variables field
- **GIVEN** a question created before variable system was added
- **WHEN** rendering the question
- **THEN** the question displays normally
- **AND** no variable substitution attempts occur

#### Scenario: Question text without variable delimiters
- **GIVEN** a question with `variables={"a": {...}}` defined
- **WHEN** question text has no `{{...}}` delimiters
- **THEN** text renders as-is without modification

#### Scenario: Migration creates nullable variables field
- **GIVEN** the variable system migration runs
- **WHEN** adding the `variables` JSONField to Question model
- **THEN** field is nullable (null=True, blank=True)
- **AND** default is None or {}
- **AND** no data migration is required for existing questions

---

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
