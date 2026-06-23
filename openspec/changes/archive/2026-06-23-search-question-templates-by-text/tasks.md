## Implementation Tasks

- [x] In `apps/questions/views.py`, filter the template queryset by trimmed
  title/question text and expose the current search term.
- [x] In `apps/questions/templates/questions/question_list.html`, add the GET
  search control and preserve `q` in pagination links.
- [x] In `apps/questions/tests.py`, add `TemplateTextSearchTests` for title,
  multilingual text, case, blank terms, choice exclusion, combined filters,
  context, UI, and pagination.
- [x] Run focused tests, the repository suite, coverage, Ruff, Django checks,
  and strict OpenSpec validation. The search tests pass and coverage is 87%;
  the suite retains one unrelated legacy string-variable test failure.
- [x] Archive the completed change.
