## ADDED Requirements

### Requirement: State field on QuestionTemplate

Add a `state` CharField to the QuestionTemplate model with choices `draft`, `completed`, `reviewed`. Default is `draft`. The field uses Django's `models.CharField` with `choices` parameter.

#### Scenario: New template defaults to draft
- **GIVEN** a user creates a new QuestionTemplate
- **WHEN** no state is explicitly provided
- **THEN** the template's state is `draft`

#### Scenario: State can be set to any valid value
- **GIVEN** a QuestionTemplate exists
- **WHEN** the state is set to `draft`, `completed`, or `reviewed`
- **THEN** the model saves successfully

#### Scenario: Invalid state is rejected
- **GIVEN** a QuestionTemplate exists
- **WHEN** the state is set to an invalid value (e.g., `archived`)
- **THEN** Django form validation rejects the value

#### Scenario: State field in edit form
- **GIVEN** the template edit form (`question_form.html`)
- **WHEN** the form is rendered
- **THEN** a `<select>` dropdown with `form-select` class appears for the state field, showing Draft, Completed, and Reviewed as options

#### Scenario: State shown on preview page
- **GIVEN** a template with state `reviewed`
- **WHEN** the preview page (`question_preview.html`) is loaded
- **THEN** the state is displayed as a badge in the template info card (e.g., `<span class="badge bg-success">Reviewed</span>`)

### Model Field Definition

- **Field:** `state = models.CharField(max_length=20, choices=TemplateState.choices, default=TemplateState.DRAFT)`
- **Choices class:** `TemplateState(models.TextChoices)` with `DRAFT = "draft", "Draft"`, `COMPLETED = "completed", "Completed"`, `REVIEWED = "reviewed", "Reviewed"`
- **Migration:** Auto-generated, adds `state` column with default `draft`
