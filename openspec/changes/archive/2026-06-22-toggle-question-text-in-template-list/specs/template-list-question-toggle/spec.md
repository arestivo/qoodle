## ADDED Requirements

### Requirement: List-level question text toggle

The question-template list MUST provide one global control that shows or hides
the question text for every template visible on the current page. The control
MUST NOT be repeated per template, and expanded content MUST NOT include answer
choices.

The feature applies to `GET /questions/`, including filtered and paginated
variants such as `/questions/?subject=123e4567-e89b-12d3-a456-426614174000`.
It introduces no model fields or constraints; it reads the existing
`QuestionTemplate.text` JSONField.

The control MUST be a Bootstrap 5.3.8
`btn btn-sm btn-outline-secondary` button in the list card header, with
`id="toggleQuestionTextBtn"`, an eye icon, and `aria-expanded="false"` in its
initial state. Question text sections MUST use Bootstrap utility classes and
MUST initially include `d-none`.

#### Scenario: Questions are hidden initially

- **GIVEN** the template list contains one or more templates
- **WHEN** the page is first rendered
- **THEN** one list-level button is labelled “Show Questions”
- **AND** its `aria-expanded` value is `false`
- **AND** all question-text sections are hidden
- **AND** no per-template question visibility buttons are rendered

#### Scenario: Show all visible questions

- **GIVEN** question text is hidden
- **WHEN** the user activates “Show Questions”
- **THEN** the question text for every template on the current page becomes visible
- **AND** the button label changes to “Hide Questions”
- **AND** its icon changes to `fa-eye-slash`
- **AND** its `aria-expanded` value becomes `true`

#### Scenario: Hide all visible questions

- **GIVEN** question text is visible
- **WHEN** the user activates “Hide Questions”
- **THEN** every question-text section on the current page becomes hidden
- **AND** the button label changes to “Show Questions”
- **AND** its icon changes to `fa-eye`
- **AND** its `aria-expanded` value becomes `false`

#### Scenario: Choices remain excluded

- **GIVEN** a template has a question and multiple answer choices
- **WHEN** question text is shown from the template list
- **THEN** only the question text is displayed
- **AND** no correct or incorrect choice text is rendered in the expanded section

#### Scenario: Toggle applies only to the loaded page

- **GIVEN** the template list is paginated
- **AND** question text is visible on the current page
- **WHEN** the user navigates to another page or changes a filter
- **THEN** the newly loaded list starts with question text hidden

### Requirement: Multilingual question text rendering

The list MUST resolve each displayed question through
`QuestionTemplate.get_text()` without directly indexing the multilingual
JSONField. This MUST preserve the existing fallback order: language-independent
`none` content first, then the first available language alphabetically when no
language is selected. The selected source text MUST be rendered using the
existing `questions` app `markdown` template filter. Variable placeholders MAY
remain visible because the list represents the template rather than a generated
question instance.

#### Scenario: Language-independent question text

- **GIVEN** a template has a `none` question-text value
- **WHEN** question text is shown in the list
- **THEN** the `none` value is displayed with Markdown rendered as HTML

#### Scenario: Fallback to an available language

- **GIVEN** a template has no `none` value and contains English and Portuguese text
- **WHEN** question text is shown in the list
- **THEN** `QuestionTemplate.get_text()` selects the first available language alphabetically
- **AND** the selected text is rendered as Markdown

### Requirement: Question-list JavaScript delivery

The toggle behavior MUST be implemented in
`apps/questions/static/questions/js/question_list.js` without inline event
handlers. The script inclusion in
`apps/questions/templates/questions/question_list.html` MUST remain deferred
inside the `extra_js` block, which is enclosed by `{% compress js %}` and
`{% endcompress %}` in `common/base.html`. No new CSS file is required.

#### Scenario: JavaScript initializes without templates

- **GIVEN** the question list is empty
- **WHEN** `question_list.js` initializes
- **THEN** it does not raise an error
- **AND** no question toggle is displayed
