## Why

The question form currently treats commas as set-item separators. This makes it
impossible to define an item such as `Paris, France` because it is stored as two
items. The canonical variable-system specification already describes set items
as one item per line, but the form implementation does not follow that contract.

## Context

Set variables are stored as an `items` array inside the existing
`QuestionTemplate.variables` JSONField. Generation already operates on complete
array entries and requires no change. The defect is limited to the set-variable
editor in `question_form.html` and its JavaScript serialization in
`question_form.js`. No new dependency is required by `pyproject.toml`.

## What Changes

- Replace the comma-separated set item input with a multiline textarea.
- Treat each non-empty line as one set item.
- Preserve commas and other punctuation inside each line.
- Display existing saved set items one per line when editing.
- Update help text and regression tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `variable-system`: set-variable form input follows the specified one-item-per-line format.

## Impact

The change affects only the question form template, its JavaScript serializer,
and tests. Stored JSON remains an array of strings, so models, migrations,
imports, exports, generation, and Django form fields remain compatible.

The primary frontend risk is trimming meaningful internal punctuation or
creating empty items from blank lines. Serialization will trim surrounding
whitespace, discard empty lines, and leave commas inside non-empty lines
unchanged.

Verification will run
`poetry run pytest apps/questions/tests.py -k SetVariableForm` and
`poetry run node --check apps/questions/static/questions/js/question_form.js`.
