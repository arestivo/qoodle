## ADDED Requirements

### Requirement: Tags input in question form

The question create/edit form includes a `tags` text input field where users enter comma-separated tags.

#### Scenario: Creating a template with tags
- **GIVEN** the user is on the question create form (`/questions/create/`)
- **WHEN** the user enters `"easy, exam-2024"` in the tags field and submits
- **THEN** the template is saved with `tags = "easy, exam-2024"`

#### Scenario: Editing tags on an existing template
- **GIVEN** a template with `tags = "easy"`
- **WHEN** the user navigates to the edit form (`/questions/<pk>/edit/`)
- **THEN** the tags field is pre-filled with `"easy"`
- **WHEN** the user changes it to `"easy, review"` and submits
- **THEN** the template is updated with `tags = "easy, review"`

#### Scenario: Clearing tags
- **GIVEN** a template with `tags = "easy, hard"`
- **WHEN** the user clears the tags field and submits
- **THEN** the template is saved with `tags = ""`

### Requirement: Tags field placement and styling

The tags input appears after the subject field in the form, using a standard Bootstrap `form-control` text input with a help text hint.

#### Scenario: Form field rendering
- **GIVEN** the question create or edit form
- **WHEN** the form renders
- **THEN** a text input labeled "Tags" appears after the subject field
- **AND** help text reads "Comma-separated tags (e.g. easy, exam-2024, review)"
