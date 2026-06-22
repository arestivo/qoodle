## Why

The question-template list shows titles and metadata but not the question
itself. Reviewing many templates therefore requires opening each preview page.
A single list-level toggle should reveal the question text for every template
on the current page, making comparison faster without adding controls to every
row or exposing answer choices.

## Context

This extends the existing `QuestionListView`, its
`apps/questions/templates/questions/question_list.html` template, and
`apps/questions/static/questions/js/question_list.js`. It reuses
`QuestionTemplate.get_text()` for the multilingual fallback defined by the
multilingual questions capability and the existing `markdown` template filter.
`pyproject.toml` already provides Django, Bootstrap, FontAwesome, and Markdown;
no new dependency is required.

## What Changes

- Add one “Show Questions” control to the template-list card header.
- Toggle question-text sections for all templates visible on the current page.
- Change the control to “Hide Questions” while text is visible.
- Render only question text; do not render choices.
- Keep question text hidden by default and reset to hidden after navigation or
  filtering.

## Capabilities

### New Capabilities

- `template-list-question-toggle`: list-level visibility control for question
  text on the question-template list.

### Modified Capabilities

None.

## Impact

The change affects the questions list view context, list template, JavaScript,
and tests in `apps/questions`. It requires no model, migration, URL, or API
changes.

The main Django/Python risk is bypassing established multilingual fallback or
Markdown rendering. The implementation must use the model fallback method and
existing template filter rather than indexing the JSON field directly.
Client-side behavior must also keep `aria-expanded` synchronized with the
visible state.

Verification will include
`poetry run pytest apps/questions/tests.py -k QuestionList` and JavaScript
behavior assertions for the single global control.
