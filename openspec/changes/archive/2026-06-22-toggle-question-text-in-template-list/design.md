## Context

`QuestionListView` renders a paginated table of templates at `/questions/`.
The table currently has one primary row per template and loads
`question_list.js` for filter behavior. Question text is multilingual Markdown
stored in `QuestionTemplate.text`; the model already provides the required
fallback through `get_text()`.

## Goals / Non-Goals

**Goals:**

- Provide one control for showing or hiding all question text on the loaded page.
- Display template question text using established language fallback and Markdown.
- Keep choices and per-template toggle controls out of the expanded content.
- Preserve table actions, selection, filters, and pagination.

**Non-Goals:**

- Persist visibility across requests or browser sessions.
- Select a display language from the list page.
- Generate variable values or display answer choices.
- Change the question preview page.

## Decisions

### 1. Prepare fallback text in QuestionListView

After pagination, `get_context_data()` will iterate the templates exposed as
`questions` and assign a transient `display_question_text` attribute using
`question.get_text()`. Calling the model method without a language invokes the
existing `none`-then-alphabetical fallback and leaves variable placeholders
unchanged.

This is presentation-only state; it does not add or modify a model field.

**Alternatives considered:**

- Index `question.text` in the template: rejected because it duplicates and can
  violate multilingual fallback rules.
- Call `render_text()`: rejected because it generates random variables, making
  the list unstable and no longer representative of the template source.
- Add a language selector: rejected as outside the requested list-level toggle.

### 2. Use one secondary table row per template

`apps/questions/templates/questions/question_list.html`, which extends
`common/base.html`, will load `question_tags` and add a hidden
`.question-text-row` immediately after each primary template row. Its single
cell spans all seven table columns and renders
`display_question_text|markdown`. No choice relation is rendered in this row.

The card header will contain exactly one `#toggleQuestionTextBtn` beside the
existing selection controls.

**Alternatives considered:**

- Add a question-text column: rejected because it permanently widens and
  lengthens the table.
- Add a toggle to every row: rejected because the requested interaction is
  global.
- Use a Bootstrap accordion per template: rejected because it implies
  per-template controls and mutual-exclusion behavior.

### 3. Keep visibility as local client state

`apps/questions/static/questions/js/question_list.js` will bind one click
handler to the global button. It toggles `d-none` on every
`.question-text-row`, then updates button text, icon, and `aria-expanded`.
State is not stored in the URL, session, or local storage, so every full page
load starts hidden.

The existing deferred scripts remain in the `extra_js` block. That block is
already nested inside `{% compress js %}` in `common/base.html`, so no nested
compressor block is added. No new CSS file, inline JavaScript, template tag, or
filter is needed; the existing `questions.markdown` filter is reused.

### 4. No database or routing changes

There are no model, field, relationship, or migration changes. The route
remains `path("", QuestionListView.as_view(), name="list")` under the questions
URL namespace, resolving to `/questions/`.

## Risks / Trade-offs

- Rendering Markdown for every template on a page adds bounded work for the
  existing 20-item page size. It avoids extra database queries.
- Hidden rows are present in the HTML, so this is a presentation toggle rather
  than lazy loading. That keeps behavior immediate and avoids a new endpoint.
- Long questions can make the expanded table tall. A global hide action gives
  the user a direct way to return to the compact view.
