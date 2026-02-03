# exam-management Specification (Delta)

## ADDED Requirements

### Requirement: Exam CRUD Operations

Teachers SHALL be able to create, view, edit, and delete exams with title, optional date, and optional description.

#### Scenario: Create exam with required title
- **GIVEN** a teacher is on the exam creation page
- **WHEN** they enter title "Midterm Exam 2026" and submit
- **THEN** a new exam is created with that title
- **AND** the exam has no date or description (optional fields empty)
- **AND** the teacher is redirected to the exam detail page

#### Scenario: Create exam with all fields
- **GIVEN** a teacher is creating an exam
- **WHEN** they enter title "Final Exam", date "2026-06-15", and description "Covers all topics"
- **THEN** the exam is created with all three fields populated
- **AND** the exam appears in the exam list

#### Scenario: Create exam without title fails
- **GIVEN** a teacher is creating an exam
- **WHEN** they leave the title field empty and submit
- **THEN** form validation fails with error "Title is required"
- **AND** the exam is not created

#### Scenario: Edit existing exam
- **GIVEN** an exam exists with title "Draft Exam"
- **WHEN** the teacher edits it to change title to "Final Version" and adds date "2026-05-20"
- **THEN** the exam is updated with new values
- **AND** the changes are visible on the exam detail page

#### Scenario: Delete exam
- **GIVEN** an exam exists with 3 question pools
- **WHEN** the teacher deletes the exam
- **THEN** the exam is removed from the database
- **AND** all associated question pools are also deleted (cascade)
- **AND** the question templates remain in the database (not deleted)

#### Scenario: View exam list
- **GIVEN** 5 exams exist in the system
- **WHEN** the teacher navigates to the exams page
- **THEN** all 5 exams are displayed
- **AND** each shows title, date (if set), and number of question pools
- **AND** exams are sorted by creation date (newest first)

---

### Requirement: Question Pool Management

Exams SHALL contain ordered question pools that can be added, removed, and reordered.

#### Scenario: Add question pool to exam
- **GIVEN** an exam exists with 2 question pools (order 1, 2)
- **WHEN** the teacher adds a new question pool
- **THEN** the new pool is created with order=3
- **AND** it appears at the bottom of the pool list

#### Scenario: Remove question pool from exam
- **GIVEN** an exam has 3 question pools (order 1, 2, 3)
- **WHEN** the teacher deletes pool with order=2
- **THEN** that pool is removed
- **AND** all question templates in that pool are unlinked (not deleted)
- **AND** remaining pools keep their original order (1, 3 - no reordering)

#### Scenario: Reorder question pools
- **GIVEN** an exam has pools with order [1, 2, 3]
- **WHEN** the teacher moves pool 3 to position 1
- **THEN** the pool orders become [3, 1, 2]
- **AND** the visual order in the UI reflects this change

#### Scenario: Empty exam has no pools initially
- **GIVEN** a newly created exam
- **WHEN** viewing the exam detail page
- **THEN** the pool list shows "No question pools yet"
- **AND** an "Add Pool" button is visible

#### Scenario: View pool count in exam list
- **GIVEN** exam A has 5 pools, exam B has 0 pools
- **WHEN** viewing the exam list
- **THEN** exam A shows "5 question pools"
- **AND** exam B shows "0 question pools"

---

### Requirement: Question Template Selection for Pools

Teachers SHALL be able to add multiple question templates to each pool with configurable version counts.

#### Scenario: Add question template to pool
- **GIVEN** a question pool exists (empty)
- **AND** a question template "Pythagorean Theorem" exists
- **WHEN** the teacher selects that template and adds it to the pool with 5 versions
- **THEN** the template is linked to the pool
- **AND** number_of_versions is set to 5
- **AND** the template appears in the pool's template list

#### Scenario: Add multiple templates to same pool
- **GIVEN** a question pool exists
- **WHEN** the teacher adds templates A, B, and C to the pool
- **THEN** all three templates are linked to the pool
- **AND** each can have a different number_of_versions
- **AND** all three appear in the pool's template list

#### Scenario: Set version count for template
- **GIVEN** adding a template to a pool
- **WHEN** the teacher sets number_of_versions to 10
- **THEN** the QuestionPoolTemplate record stores 10
- **AND** this value will be used during Moodle export (future)

#### Scenario: Version count defaults to 1
- **GIVEN** adding a template to a pool
- **WHEN** the teacher does not specify a version count
- **THEN** number_of_versions defaults to 1

#### Scenario: Version count must be positive
- **GIVEN** adding a template to a pool
- **WHEN** the teacher enters number_of_versions as 0 or negative
- **THEN** validation fails with error "Version count must be at least 1"
- **AND** the template is not added to the pool

#### Scenario: Remove template from pool
- **GIVEN** a pool contains template A with 5 versions
- **WHEN** the teacher removes that template from the pool
- **THEN** the QuestionPoolTemplate link is deleted
- **AND** the template itself remains in the database (not deleted)
- **AND** it can be added to other pools

---

### Requirement: Duplicate Template Prevention

The same question template SHALL NOT appear in multiple pools within the same exam.

#### Scenario: Prevent adding same template to different pools
- **GIVEN** exam has pool 1 containing template A
- **AND** exam has pool 2 (empty)
- **WHEN** the teacher tries to add template A to pool 2
- **THEN** validation fails with error "Template already used in this exam (Pool 1)"
- **AND** the template is not added to pool 2

#### Scenario: Same template can appear in different exams
- **GIVEN** exam X has pool containing template A
- **AND** exam Y exists (different exam)
- **WHEN** the teacher adds template A to a pool in exam Y
- **THEN** the operation succeeds
- **AND** template A now appears in both exams (different pools)

#### Scenario: UI disables already-used templates
- **GIVEN** exam has pool 1 containing templates A and B
- **WHEN** the teacher opens the template selection UI for pool 2
- **THEN** templates A and B are disabled/grayed out
- **AND** other templates remain selectable
- **AND** a tooltip shows "Already used in Pool 1"

#### Scenario: Removing template re-enables it for other pools
- **GIVEN** exam has template A in pool 1 (disabled for pool 2)
- **WHEN** the teacher removes template A from pool 1
- **THEN** template A becomes available for pool 2
- **AND** the UI no longer shows it as disabled

---

### Requirement: Template Filtering by Subject

When selecting templates for a pool, teachers SHALL be able to filter by subject to find relevant questions.

#### Scenario: Filter templates by subject
- **GIVEN** 20 templates exist (10 in "Mathematics", 5 in "Physics", 5 in "Chemistry")
- **WHEN** the teacher filters by subject "Mathematics"
- **THEN** only the 10 mathematics templates are displayed
- **AND** templates from other subjects are hidden

#### Scenario: Show all templates when no filter
- **GIVEN** templates exist across multiple subjects
- **WHEN** the teacher clears the subject filter
- **THEN** all templates are displayed
- **AND** they are grouped by subject

#### Scenario: Show template count per subject in filter
- **GIVEN** 10 math templates, 5 physics templates
- **WHEN** viewing the subject filter dropdown
- **THEN** "Mathematics (10)" and "Physics (5)" are shown
- **AND** empty subjects are not listed

#### Scenario: Filter persists during selection
- **GIVEN** teacher has filtered to "Mathematics"
- **AND** selected 3 templates
- **WHEN** they add those templates to the pool
- **THEN** the filter remains active
- **AND** they can continue selecting more math templates

---

### Requirement: Bulk Pool Creation

Teachers SHALL be able to add multiple empty question pools at once to quickly scaffold an exam structure.

#### Scenario: Add 5 empty pools at once
- **GIVEN** an exam exists with 0 pools
- **WHEN** the teacher clicks "Add Multiple Pools" and enters quantity 5
- **THEN** 5 empty question pools are created
- **AND** they have sequential order (1, 2, 3, 4, 5)
- **AND** all appear in the pool list

#### Scenario: Add pools to existing exam
- **GIVEN** an exam has 3 pools (order 1-3)
- **WHEN** the teacher adds 2 more pools
- **THEN** new pools are created with order 4 and 5
- **AND** existing pools remain unchanged

#### Scenario: Bulk creation validates quantity
- **GIVEN** adding multiple pools
- **WHEN** quantity is 0 or negative
- **THEN** validation fails with error "Must add at least 1 pool"

#### Scenario: Maximum pool limit
- **GIVEN** adding multiple pools
- **WHEN** quantity would exceed 100 pools in one exam
- **THEN** validation fails with error "Cannot exceed 100 pools per exam"
- **AND** no pools are created

---

### Requirement: Navigation Integration

The exam management feature SHALL be accessible via main navigation, replacing the placeholder "Manage Languages" link.

#### Scenario: Navigate to exams from main menu
- **GIVEN** a teacher is logged in
- **WHEN** they view the main navigation
- **THEN** "Manage Exams" link is visible
- **AND** "Manage Languages" link is NOT visible (removed)

#### Scenario: Exams link shows active state
- **GIVEN** teacher is on any exam page (list, detail, create)
- **WHEN** viewing the navigation
- **THEN** the "Manage Exams" link has the active/highlighted state

#### Scenario: Navigate between exams and question templates
- **GIVEN** teacher is viewing an exam detail page
- **WHEN** they click "Manage Question Templates" in navigation
- **THEN** they are taken to the question template list
- **AND** can navigate back to exams via the "Manage Exams" link

---

### Requirement: Exam Detail View

The exam detail page SHALL display comprehensive information including metadata, pool list, and template distribution.

#### Scenario: View exam with pools and templates
- **GIVEN** an exam has title, date, description
- **AND** 3 pools containing [2 templates, 3 templates, 1 template]
- **WHEN** viewing the exam detail page
- **THEN** title, date, description are displayed at the top
- **AND** all 3 pools are listed in order
- **AND** each pool shows its template count and template titles
- **AND** total template count (6) is shown

#### Scenario: Show version count per template
- **GIVEN** pool 1 has template A (5 versions), template B (3 versions)
- **WHEN** viewing the exam detail page
- **THEN** pool 1 displays:
  - "Template A (5 versions)"
  - "Template B (3 versions)"

#### Scenario: Show empty pools clearly
- **GIVEN** an exam has pool 2 with no templates
- **WHEN** viewing the exam detail page
- **THEN** pool 2 shows "No templates yet"
- **AND** an "Add Templates" button is visible for that pool

#### Scenario: Navigate to template preview from exam
- **GIVEN** exam detail page shows template A in pool 1
- **WHEN** the teacher clicks on template A's title
- **THEN** they are taken to the template preview page
- **AND** can see the template's variables and sample questions

---
