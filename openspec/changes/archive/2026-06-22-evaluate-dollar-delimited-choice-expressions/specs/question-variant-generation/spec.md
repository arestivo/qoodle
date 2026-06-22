## MODIFIED Requirements

### Requirement: Choice Text Variable Substitution

Generated answer choices MUST apply the same `{{...}}` variable substitution as
question text and MUST then evaluate complete `$expression$` segments using the
same generated variable values. Invalid or unmatched dollar expressions MUST
remain literal.

For each choice in the template, the system extracts text in the target
language, applies substitution with the question variant's generated values,
and renders the result as Markdown HTML.

#### Scenario: Substitute variables in choices

- **GIVEN** question: "Calculate {{x}} + {{y}}"
- **AND** choice texts: "{{x}}", "{{y}}", "{{x}} + {{y}}", "0"
- **AND** seed generates x=5, y=3
- **WHEN** variant choices are generated
- **THEN** question text is "Calculate 5 + 3"
- **AND** choice 1 is "5"
- **AND** choice 2 is "3"
- **AND** choice 3 is "8"
- **AND** choice 4 is "0"

#### Scenario: Moodle variant evaluates dollar-delimited choice

- **GIVEN** a question variant generates `x=5` and `y=3`
- **AND** a choice contains `$x + y$`
- **WHEN** the variant choices are generated
- **THEN** that choice text is `8`
- **AND** Moodle XML contains the evaluated value rather than `$x + y$`
