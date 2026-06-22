## Why

String-variable options are currently entered as a comma-separated string.
Values such as `Paris, France` are therefore split into separate options. The
editor should use the same explicit one-value-per-line format as set variables.

## Context

String variables are stored in `QuestionTemplate.variables` as a JSON `values`
array. The generator already selects complete array entries correctly. Only the
question-form template and JavaScript editor convert that array to and from
comma-separated text. No new dependency is required.

## What Changes

- Replace the string-value input with a multiline textarea.
- Treat each non-empty trimmed line as one option.
- Preserve commas inside each line.
- Load existing options one per line during editing.
- Update help text and regression tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `string-variable-type`: string-variable values use one-option-per-line UI.
- `variable-system`: the variable-definition form uses newline-delimited string options.

## Impact

No database, model, migration, URL, import, export, or generator changes are
required. Existing saved arrays remain compatible and will be shown one entry
per line when edited.

Serialization trims surrounding whitespace and ignores blank lines while
preserving internal punctuation. Verification will run
`poetry run pytest apps/questions/tests.py -k StringVariableForm` and
`poetry run node --check apps/questions/static/questions/js/question_form.js`.
