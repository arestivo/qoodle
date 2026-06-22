## Why

Choice text can currently substitute `{{...}}` expressions, but some imported
or authored choices use `$expression$` to indicate that the enclosed value
must be calculated. Those choices are currently exported and previewed
literally instead of producing the evaluated answer.

## Context

`Choice.get_text()` already delegates variable substitution to its
`QuestionTemplate`, and `VariableGenerator.evaluate_expression()` provides the
restricted evaluation context used elsewhere by the variable system. This
change reuses that evaluator for dollar-delimited expressions in choices only.
`pyproject.toml` confirms no new dependency is required.

## What Changes

- Evaluate every complete `$expression$` segment in choice text.
- Evaluate against the same generated variables used by the question variant.
- Apply normal `{{...}}` substitution before dollar-expression evaluation.
- Preserve unmatched or invalid dollar expressions literally.
- Leave question text and ordinary choices unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `variable-system`: choice text supports `$...$` as an additional expression
  delimiter.
- `question-variant-generation`: generated choices contain evaluated
  dollar-delimited values.

## Impact

The change is limited to question model text rendering and tests. There are no
model fields, migrations, URLs, templates, static files, or dependencies.

The main Python risk is unsafe expression execution. Evaluation must continue
through the existing restricted evaluator with empty `__builtins__` and its
explicit safe-function allowlist. Another compatibility risk is currency or
math text enclosed by paired dollar signs; by definition, complete paired
delimiters opt into evaluation, while unmatched dollar signs remain literal.

Verification will run
`poetry run pytest apps/questions/tests.py -k DollarDelimitedChoiceExpression`
and the Moodle XML generation tests.
