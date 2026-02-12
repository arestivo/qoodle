## Implementation Tasks

- [x] Add `tags` CharField and `tag_list()` method to `QuestionTemplate` in `apps/questions/models.py`
- [x] Generate and apply migration: `poetry run python manage.py makemigrations questions && poetry run python manage.py migrate`
- [x] Add `tags` field to `QuestionForm` in `apps/questions/forms.py` — update `fields` list and `widgets` dict
- [x] Add tag badges to question list template `apps/questions/templates/questions/question_list.html`
- [x] Add tag badges to pool template add view `apps/exams/templates/exams/pool_template_add.html`
- [x] Add tests for `tag_list()` method in `apps/questions/tests.py` (empty, normal, whitespace cases)
- [x] Verify: run `poetry run pytest` and confirm all tests pass
