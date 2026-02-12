## Implementation Tasks

- [x] Add `TemplateState` TextChoices class and `state` CharField to QuestionTemplate in `apps/questions/models.py`, add index on `state` field
- [x] Generate and apply migration: `poetry run python manage.py makemigrations questions && poetry run python manage.py migrate`
- [x] Add `state` to QuestionForm fields and widgets in `apps/questions/forms.py` (Select widget with `form-select` class)
- [x] Add state `<select>` field to the edit form template `apps/questions/templates/questions/question_form.html` between tags and question text
- [x] Add state filter to `QuestionListView` in `apps/questions/views.py`: read `state` GET param, filter queryset, pass `selected_state` to context
- [x] Add state filter dropdown and reviewed checkmark to `apps/questions/templates/questions/question_list.html`: add `<select name="state">` in filter card, add green checkmark after title for reviewed templates, update pagination links to include state param
- [x] Add state select to auto-submit listener in `apps/questions/static/questions/js/question_list.js`
- [x] Add state badge to preview page `apps/questions/templates/questions/question_preview.html` (color-coded: draft=warning, completed=info, reviewed=success)
- [x] Add reviewed checkmark to exam detail `apps/exams/templates/exams/exam_detail.html` inline after template title
- [x] Add reviewed checkmark to pool template add `apps/exams/templates/exams/pool_template_add.html` inline after template title
- [x] Filter pool template add to reviewed-only in `PoolTemplateAddView.get_context_data()` in `apps/exams/views.py`
- [x] Add tests for state field defaults, state filter in list view, and reviewed-only restriction in pool template add view in `apps/questions/tests.py`
- [x] Run tests: `poetry run python manage.py test apps.questions apps.exams`
