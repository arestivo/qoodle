## Implementation Tasks

- [x] In `apps/questions/views.py`, update `QuestionListView.get_context_data()`
  to expose each visible template's question text through
  `QuestionTemplate.get_text()` without generating variables.
- [x] In
  `apps/questions/templates/questions/question_list.html`, load
  `question_tags`, add one list-header “Show Questions” button, and add one
  initially hidden question-text row after each template row; render Markdown
  and do not render choices.
- [x] In `apps/questions/templates/questions/question_list.html`, keep the
  deferred question-list and bulk-action scripts in the `extra_js` block so
  they remain covered by the parent template's `{% compress js %}` block.
- [x] In `apps/questions/static/questions/js/question_list.js`, implement the
  single global show/hide interaction and synchronize its label, FontAwesome
  icon, and `aria-expanded` state.
- [x] In `apps/questions/tests.py`, add list-view tests for one global control,
  hidden-by-default rows, multilingual fallback, Markdown output, retained
  variable placeholders, and absence of choice text in expanded content.
- [x] Verify the focused list behavior with
  `poetry run pytest apps/questions/tests.py -k QuestionList`.
- [x] Verify repository coverage remains at least 80% with
  `poetry run pytest` (85% coverage; one unrelated pre-existing string-variable
  test failure remains).
- [x] Run `poetry run ruff check apps/questions/views.py`,
  `poetry run node --check apps/questions/static/questions/js/question_list.js`,
  and
  `poetry run openspec validate toggle-question-text-in-template-list --strict`.
