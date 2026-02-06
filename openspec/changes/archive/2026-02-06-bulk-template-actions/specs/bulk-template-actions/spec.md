## ADDED Requirements

### Requirement: Template Selection UI

The question list page displays checkboxes for selecting multiple templates.

#### Scenario: Checkbox column in template table
- **WHEN** viewing the question list page
- **THEN** each template row has a checkbox in the first column
- **THEN** clicking the checkbox selects/deselects that template
- **THEN** clicking the row (outside the checkbox) still navigates to preview

#### Scenario: Select All / Select None controls
- **WHEN** viewing the question list page
- **THEN** the table header includes "Select All" and "Select None" buttons
- **THEN** clicking "Select All" checks all visible template checkboxes
- **THEN** clicking "Select None" unchecks all template checkboxes

#### Scenario: Selection persists during pagination
- **WHEN** templates are selected on page 1
- **AND** user navigates to page 2
- **THEN** selections on page 1 are preserved (stored in hidden form or JavaScript state)

---

### Requirement: Bulk Action Bar

A sticky action bar appears when templates are selected.

#### Scenario: Action bar visibility
- **WHEN** no templates are selected
- **THEN** the bulk action bar is hidden

#### Scenario: Action bar appears on selection
- **WHEN** one or more templates are selected
- **THEN** a sticky action bar appears at the bottom of the viewport
- **THEN** the bar shows the count of selected templates (e.g., "3 templates selected")

#### Scenario: Action bar contents
- **WHEN** the bulk action bar is visible
- **THEN** it contains:
  - Selected count badge
  - Subject dropdown for "Move to" action
  - "Move" button
  - "Delete" button (styled as danger)
  - "Clear Selection" button

---

### Requirement: Bulk Move to Subject

Selected templates can be moved to a different subject.

#### Scenario: Move templates to subject
- **GIVEN** 3 templates are selected
- **WHEN** user selects a subject from the dropdown and clicks "Move"
- **THEN** all 3 templates are updated with the new subject
- **THEN** a success message shows "3 templates moved to [Subject Name]"
- **THEN** the page refreshes showing the updated list

#### Scenario: Move with current filter active
- **GIVEN** viewing templates filtered by "Subject A"
- **AND** 2 templates are selected
- **WHEN** user moves them to "Subject B"
- **THEN** the templates disappear from the current view (filter still active)
- **THEN** success message confirms the move

#### Scenario: Move URL pattern
- **WHEN** submitting the move action
- **THEN** POST to `/questions/bulk-move/`
- **THEN** request body contains `template_ids[]` and `subject_id`

---

### Requirement: Bulk Delete

Selected templates can be deleted with confirmation.

#### Scenario: Delete confirmation
- **GIVEN** 5 templates are selected
- **WHEN** user clicks "Delete"
- **THEN** a confirmation modal appears
- **THEN** modal shows "Delete 5 templates? This action cannot be undone."
- **THEN** modal has "Cancel" and "Delete" buttons

#### Scenario: Confirm delete
- **GIVEN** the delete confirmation modal is shown
- **WHEN** user clicks "Delete" in the modal
- **THEN** all selected templates and their choices are deleted
- **THEN** success message shows "5 templates deleted"
- **THEN** the page refreshes

#### Scenario: Cancel delete
- **GIVEN** the delete confirmation modal is shown
- **WHEN** user clicks "Cancel"
- **THEN** the modal closes
- **THEN** no templates are deleted
- **THEN** selections remain intact

#### Scenario: Delete URL pattern
- **WHEN** submitting the delete action
- **THEN** POST to `/questions/bulk-delete/`
- **THEN** request body contains `template_ids[]`

---

### Requirement: Error Handling

Bulk operations handle errors gracefully.

#### Scenario: Partial failure on move
- **GIVEN** 3 templates are selected for move
- **WHEN** 1 template fails to update (e.g., database error)
- **THEN** show error: "Failed to move 1 template. 2 templates moved successfully."
- **THEN** successful moves are committed

#### Scenario: No templates selected
- **WHEN** user clicks "Move" or "Delete" with no templates selected
- **THEN** show warning: "Please select at least one template"
- **THEN** no action is performed

#### Scenario: Invalid subject for move
- **WHEN** user clicks "Move" without selecting a subject
- **THEN** show warning: "Please select a destination subject"
- **THEN** no action is performed
