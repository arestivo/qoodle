## Implementation Tasks

- [x] In `apps/questions/models.py`, add a restricted helper for evaluating
  complete `$...$` segments and formatting their results.
- [x] In `apps/questions/models.py`, update `Choice.get_text()` to run normal
  substitution followed by dollar-expression evaluation only when a variable
  context is supplied.
- [x] In `apps/questions/tests.py`, add
  `DollarDelimitedChoiceExpressionTests` covering whole, embedded, multiple,
  set-index, post-substitution, constant, invalid, unmatched, and
  question-text-exclusion cases.
- [x] In `apps/exams/tests.py`, add Moodle export regression coverage proving a
  dollar-delimited choice is exported as its evaluated value.
- [x] Verify focused behavior with
  `poetry run pytest apps/questions/tests.py -k DollarDelimitedChoiceExpression`
  and `poetry run pytest apps/exams/tests.py -k dollar_delimited_choice_expression`.
- [x] Run `poetry run ruff check apps/questions/models.py`,
  `poetry run python manage.py check`, and
  `poetry run openspec validate evaluate-dollar-delimited-choice-expressions --strict`.
- [x] Archive the completed OpenSpec change.
