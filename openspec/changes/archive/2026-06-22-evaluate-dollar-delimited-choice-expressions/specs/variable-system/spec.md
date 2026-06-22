## MODIFIED Requirements

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
