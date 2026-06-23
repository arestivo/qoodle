## ADDED Requirements

### Requirement: Duplicate exam with question structure

The system MUST allow a teacher to duplicate an exam through
`POST /exams/<uuid:pk>/duplicate/`. The operation MUST create new `Exam`,
`QuestionPool`, and `QuestionPoolTemplate` UUID records in one atomic
transaction. Existing `QuestionTemplate` records MUST be reused rather than
cloned.

#### Scenario: Duplicate a populated exam

- **GIVEN** an exam with title, date, description, grading mode, ordered pools,
  grades, template assignments, and version counts
- **WHEN** the teacher duplicates the exam
- **THEN** a new exam is created with title `<original title> (Copy)`
- **AND** date, description, and grading mode match the original
- **AND** all pools are copied with the same order and default grade
- **AND** all pool-template assignments preserve their template and version count
- **AND** the original exam and its structure remain unchanged

#### Scenario: Reuse shared templates

- **GIVEN** a source pool references a question template
- **WHEN** its exam is duplicated
- **THEN** the copied pool membership references the same question template UUID
- **AND** no new `QuestionTemplate` is created

#### Scenario: Duplicate an empty exam

- **GIVEN** an exam has no pools
- **WHEN** it is duplicated
- **THEN** a new exam with no pools is created successfully

#### Scenario: Duplicate title stays within model limit

- **GIVEN** an exam title is at the `CharField(max_length=255)` limit
- **WHEN** it is duplicated
- **THEN** the source title is truncated as needed before appending ` (Copy)`
- **AND** the duplicate title is no longer than 255 characters

#### Scenario: Duplicate request succeeds

- **WHEN** a valid duplicate POST request completes
- **THEN** the user is redirected to the new exam detail page
- **AND** a success message identifies the new exam

### Requirement: Exam duplication controls

The exam list and exam detail page MUST each provide a Bootstrap 5.3.8
`btn-outline-secondary` duplicate control using the FontAwesome
`fa-copy` icon. Each control MUST submit a POST form with CSRF protection; a
GET request MUST NOT duplicate an exam. No CSS or JavaScript is required.

#### Scenario: Duplicate from exam list

- **GIVEN** an exam appears in the exam list
- **WHEN** the list is rendered
- **THEN** its actions include a POST duplicate button

#### Scenario: Duplicate from exam detail

- **GIVEN** the teacher views an exam detail page
- **WHEN** the page is rendered
- **THEN** the header actions include a POST duplicate button
