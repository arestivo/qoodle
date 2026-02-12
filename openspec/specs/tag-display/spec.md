## ADDED Requirements

### Requirement: Tag badges in question list

Tags are displayed as Bootstrap `badge bg-secondary` elements in the question list table, wrapped in a `d-flex gap-1` container next to the template title.

#### Scenario: Template with tags in question list
- **GIVEN** a template with `tags = "easy, exam-2024"`
- **WHEN** the question list page (`/questions/`) is rendered
- **THEN** a `<div class="d-flex gap-1">` container appears next to the template title containing two `<span class="badge bg-secondary">` elements: one for "easy" and one for "exam-2024"

#### Scenario: Template with no tags in question list
- **GIVEN** a template with `tags = ""`
- **WHEN** the question list page is rendered
- **THEN** no tag badges are shown for that template

### Requirement: Tag badges in pool template add view

Tags are displayed as Bootstrap `badge bg-secondary` elements in the pool template add list, wrapped in a `d-flex gap-1` container alongside existing badges (variables/no-variables).

#### Scenario: Template with tags in pool template add
- **GIVEN** an exam pool add-templates page (`/exams/<exam_pk>/pools/<pool_pk>/templates/add/`)
- **AND** a template with `tags = "review, hard"`
- **WHEN** the page is rendered
- **THEN** a `<div class="d-flex gap-1">` container with `<span class="badge bg-secondary">` elements for "review" and "hard" appears alongside the template entry

#### Scenario: Template with no tags in pool template add
- **GIVEN** a template with no tags
- **WHEN** the pool template add page is rendered
- **THEN** no tag badges appear for that template (existing variable badges are unaffected)
