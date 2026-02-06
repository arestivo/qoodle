## Context

The question list page (`apps/questions/templates/questions/question_list.html`) currently displays templates in a table with individual action buttons. The existing `pool_template_add.html` provides a reference implementation for checkbox selection with "Select All/None" controls.

## Goals / Non-Goals

**Goals:**
- Add checkbox selection to the question list page
- Implement bulk move and bulk delete operations
- Reuse existing UI patterns from `pool_template_add.html`
- Handle pagination with selection state

**Non-Goals:**
- Adding other bulk operations (duplicate, export)
- Changing the QuestionTemplate model
- Adding undo functionality for bulk delete

## Decisions

### 1. Use Form-Based Submission (Not AJAX)

Submit bulk actions via standard form POST, not AJAX. This matches the existing application patterns and simplifies error handling.

**Alternatives considered:**
- AJAX with JSON responses: More complex, requires additional error handling UI

### 2. JavaScript Selection State (Not Hidden Fields)

Store selection state in JavaScript using a Set of template IDs. Serialize to hidden inputs on form submit. This handles pagination cleanly.

**Alternatives considered:**
- Server-side session storage: Requires more roundtrips
- Hidden input per checkbox: Loses state on pagination

### 3. Sticky Bottom Action Bar

Use Bootstrap's `position-fixed` with `bottom-0` for the action bar. Only visible when `selectedCount > 0`.

**Alternatives considered:**
- Inline buttons in header: Less visible, clutters existing UI
- Modal with actions: Extra click required

### 4. New Function-Based Views for Bulk Operations

Add two new views in `apps/questions/views.py`:
- `bulk_move_templates(request)` - POST handler for move
- `bulk_delete_templates(request)` - POST handler for delete

**Alternatives considered:**
- Class-based views: Overkill for simple POST handlers

### 5. URL Structure

Add to `apps/questions/urls.py`:
```python
path("bulk-move/", views.bulk_move_templates, name="bulk_move"),
path("bulk-delete/", views.bulk_delete_templates, name="bulk_delete"),
```

### 6. Confirmation Modal for Delete

Use Bootstrap's modal component for delete confirmation. The modal is defined in the template and triggered by JavaScript.

### 7. Static File Location

Add new JavaScript file: `apps/questions/static/questions/js/bulk_actions.js`

This handles:
- Selection state management
- Action bar visibility toggle
- Form submission with selected IDs
- Delete confirmation modal control

## Risks / Trade-offs

- **Pagination selection**: Users might not realize selections persist across pages. Mitigate with clear count display.
- **Large selections**: Bulk deleting hundreds of templates could be slow. Acceptable for typical use case.
- **Browser back button**: Selection state is lost on browser back. Acceptable given the nature of bulk operations.
