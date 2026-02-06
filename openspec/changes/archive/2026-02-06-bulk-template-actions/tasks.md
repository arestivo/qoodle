# Tasks: Bulk Template Actions

## Phase 1: Backend Views

- [x] Add `bulk_move_templates` view in `apps/questions/views.py`
- [x] Add `bulk_delete_templates` view in `apps/questions/views.py`
- [x] Add URL patterns for bulk-move and bulk-delete in `apps/questions/urls.py`

## Phase 2: Template Updates

- [x] Add checkbox column to template table in `apps/questions/templates/questions/question_list.html`
- [x] Add Select All/None buttons to table header
- [x] Add bulk action bar (sticky bottom) with move dropdown and delete button
- [x] Add delete confirmation modal

## Phase 3: JavaScript

- [x] Create `apps/questions/static/questions/js/bulk_actions.js`
- [x] Implement selection state management (Set of IDs)
- [x] Implement action bar visibility toggle
- [x] Implement form submission with selected IDs
- [x] Implement delete modal control
- [x] Include script in question_list.html

## Phase 4: Verification

- [ ] Test checkbox selection and Select All/None
- [ ] Test bulk move with subject filter active
- [ ] Test bulk delete with confirmation
- [ ] Test selection persists across pagination
- [ ] Test error handling (no selection, no subject)
