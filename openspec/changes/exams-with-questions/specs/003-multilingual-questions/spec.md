# multilingual-questions Specification (Delta)

## RENAMED Models

### Model Rename: Question → QuestionTemplate

The `Question` model SHALL be renamed to `QuestionTemplate` to better reflect its purpose as a template that generates multiple question instances through variable substitution.

#### Scenario: Database migration renames table
- **GIVEN** the Question model exists in the database
- **WHEN** running the RenameModel migration
- **THEN** the table `questions_question` is renamed to `questions_questiontemplate`
- **AND** all foreign keys are automatically updated
- **AND** existing data is preserved

#### Scenario: Choice foreign key updates
- **GIVEN** Choice model has `question` ForeignKey to Question
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** the foreign key field is renamed to `template`
- **AND** the related_name becomes `choices` on QuestionTemplate
- **AND** existing choice-question relationships are preserved

#### Scenario: Admin interface updates
- **GIVEN** QuestionAdmin class exists
- **WHEN** the model is renamed
- **THEN** admin registration uses QuestionTemplate
- **AND** the admin list page shows "Question Templates"
- **AND** all admin functionality (list, edit, delete) works unchanged

#### Scenario: View references update
- **GIVEN** views import Question model
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** all imports change to `from apps.questions.models import QuestionTemplate`
- **AND** all queryset operations use QuestionTemplate
- **AND** view logic remains functionally identical

#### Scenario: Template references update
- **GIVEN** templates reference `question` context variable
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** templates use `template` or keep `question` for backwards compatibility
- **AND** all template filters and tags work unchanged

#### Scenario: URL patterns remain the same
- **GIVEN** URLs use `/questions/` paths
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** URL paths remain `/questions/` (no change)
- **AND** URL names remain `questions:list`, `questions:create`, etc.
- **AND** users see no difference in URLs

#### Scenario: Form labels updated for clarity
- **GIVEN** QuestionForm exists
- **WHEN** Question is renamed to QuestionTemplate  
- **THEN** form help text references "question template"
- **AND** page titles say "Create Question Template"
- **AND** buttons say "Save Template"

#### Scenario: Navigation labels updated
- **GIVEN** navigation shows "Manage Questions"
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** navigation shows "Manage Question Templates"
- **AND** breadcrumbs show "Question Templates"

#### Scenario: Test suite passes after rename
- **GIVEN** existing test suite for Question model
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** all tests are updated to use QuestionTemplate
- **AND** all existing tests pass without modification
- **AND** no functionality regressions occur

#### Scenario: Related name on Subject remains intuitive
- **GIVEN** Subject has `questions` related_name
- **WHEN** Question is renamed to QuestionTemplate
- **THEN** related_name becomes `question_templates`
- **AND** `subject.question_templates.all()` returns all templates for that subject

---

## MODIFIED Requirements

### Requirement: Question Template CRUD Operations (RENAMED)

Teachers SHALL be able to create, read, update, and delete question templates (previously "questions") with all existing functionality preserved.

#### Scenario: Create question template (unchanged functionality)
- **GIVEN** a teacher is creating a new question template
- **WHEN** they enter title, subject, question text, and choices
- **THEN** a QuestionTemplate instance is created
- **AND** all validation rules apply as before
- **AND** the workflow is identical to previous Question creation

#### Scenario: List question templates with new terminology
- **GIVEN** 10 question templates exist
- **WHEN** viewing the question template list page
- **THEN** page title shows "Question Templates"
- **AND** all 10 templates are displayed
- **AND** filtering by subject still works

#### Scenario: Variable generation uses template terminology
- **GIVEN** a question template has variables defined
- **WHEN** previewing the template
- **THEN** preview page explains "This template will generate different questions"
- **AND** variable substitution works identically

---

## ADDED Integration

### Requirement: QuestionTemplate Integration with Exam System

Question templates SHALL be selectable for inclusion in exam question pools, enabling reuse across multiple exams.

#### Scenario: Question template shows pool membership
- **GIVEN** a question template is used in 3 exam pools
- **WHEN** viewing the template detail page
- **THEN** a section shows "Used in 3 exam pools"
- **AND** links to each exam are provided

#### Scenario: Deleting template with pool memberships
- **GIVEN** a question template is used in 2 exam pools
- **WHEN** attempting to delete the template
- **THEN** a warning shows "Template is used in 2 exams"
- **AND** teacher must confirm deletion understanding pools will be affected
- **AND** deletion removes template from all pools (cascade)

#### Scenario: Template list shows usage count
- **GIVEN** viewing question template list
- **WHEN** templates have varying pool memberships
- **THEN** each template shows usage count (e.g., "Used in 5 exams")
- **AND** unused templates show "Not used yet"

---
