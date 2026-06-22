## Implementation Tasks

- [x] In
  `apps/questions/templates/questions/question_form.html`, replace the set-item
  text input with a Bootstrap textarea and update its one-item-per-line help.
- [x] In `apps/questions/static/questions/js/question_form.js`, load set items
  with newline joins and serialize non-empty trimmed lines without splitting
  commas.
- [x] In `apps/questions/tests.py`, add `SetVariableFormTests` covering the
  textarea contract, comma-containing stored items, and unchanged generator
  output.
- [x] Verify focused behavior with
  `poetry run pytest apps/questions/tests.py -k SetVariableForm`.
- [x] Verify JavaScript syntax with
  `poetry run node --check apps/questions/static/questions/js/question_form.js`
  and Django configuration with `poetry run python manage.py check`.
- [x] Run `poetry run openspec validate support-commas-in-set-variable-items --strict`
  and archive the completed change.
