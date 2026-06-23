## ADDED Requirements

### Requirement: Exam detail subject links

Subject names displayed for question-pool templates on the exam detail page MUST
link to the question template list filtered by that subject.

#### Scenario: Pool template subject link includes subject UUID

- **GIVEN** an exam contains a question pool with a template assigned to a subject
- **WHEN** the exam detail page is rendered
- **THEN** the subject link targets the question template list
- **AND** the link includes the subject UUID in the `subject` query parameter
