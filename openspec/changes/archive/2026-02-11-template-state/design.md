## Context

The QuestionTemplate model in `apps/questions/models.py` currently has no lifecycle state. This design adds a `state` CharField with a `TemplateState` TextChoices class, visual indicators across templates views, a filter on the list page, and a restriction on exam template selection.

## Goals / Non-Goals

**Goals:**
- Add a `state` field to QuestionTemplate with draft/completed/reviewed choices
- Show a green checkmark for reviewed templates in all listing views
- Add a state filter to the template list page
- Restrict exam template selection to reviewed-only templates
- Include state in the edit form and preview page

**Non-Goals:**
- State transition enforcement (any state can be set to any other state freely)
- Permissions or role-based state changes
- Bulk state change action (may be added later)

## Decisions

### 1. Use Django TextChoices for state values

Define `TemplateState(models.TextChoices)` in `apps/questions/models.py` above the QuestionTemplate class. Values: `DRAFT = "draft"`, `COMPLETED = "completed"`, `REVIEWED = "reviewed"`.

Use `CharField(max_length=20, choices=TemplateState.choices, default=TemplateState.DRAFT)` on the model.

**Alternatives considered:**
- IntegerField with IntegerChoices: Rejected — string values are more readable in the database and templates.

### 2. Database schema change

Add `state` column to `questions_questiontemplate` table:
- `CharField(max_length=20)` with default `"draft"`
- Add database index on `state` field for efficient filtering: `models.Index(fields=["state"])`

Migration auto-generated via `makemigrations`.

### 3. Form field placement

Add `state` to `QuestionForm.Meta.fields` after `tags`. Use the default `Select` widget with `form-select` class. The form template `question_form.html` renders fields manually, so add the state `<select>` block between tags and question text.

### 4. State filter in template list view

In `QuestionListView.get_queryset()`, read `self.request.GET.get("state")` and filter the queryset with `.filter(state=state_value)` when provided. Pass `selected_state` to template context.

In `question_list.html`, add a `<select name="state">` dropdown in the existing filter form card, in a new `col-md-4` column. The subject filter column shrinks from `col-md-8` to `col-md-4` to make room. The state dropdown auto-submits on change via JavaScript (same pattern as subject filter in `question_list.js`).

Pagination links must include `&state={{ selected_state }}` when active.

### 5. State display in template list

In `question_list.html`, add a green checkmark icon `<i class="fa-solid fa-circle-check text-success" title="Reviewed">` right after the template title in the title `<td>`, conditionally rendered with `{% if question.state == "reviewed" %}`.

### 6. State display in exam detail and pool template add

In `exam_detail.html`, add the checkmark inline after `<strong>{{ pt.template.title }}</strong>`, conditionally rendered with `{% if pt.template.state == "reviewed" %}`.

In `pool_template_add.html`, add the checkmark inline after `<strong>{{ template.title }}</strong>` in the same `d-flex` container, with the same condition.

### 7. State badge on preview page

In `question_preview.html`, add a state badge after the "Updated" line in the info card. Use color-coded badges:
- `draft`: `badge bg-warning text-dark`
- `completed`: `badge bg-info`
- `reviewed`: `badge bg-success`

Use `question.get_state_display` for the label.

### 8. Exam template selection restriction

In `PoolTemplateAddView.get_context_data()` in `apps/exams/views.py`, chain `.filter(state="reviewed")` on the `available_templates` queryset. This is applied after the existing `.exclude(id__in=existing_template_ids)`.

### 9. URL routing

No new URL patterns needed. All changes are to existing views and templates.

### 10. Template inheritance

No changes to template inheritance hierarchy. All templates already extend `common/base.html`.

### 11. Static files

No new static files needed. The filter form auto-submit is handled by the existing `question_list.js` which already listens for changes on the subject select — add the state select to the same listener.

## Files Modified

- `apps/questions/models.py` — Add `TemplateState` class and `state` field
- `apps/questions/forms.py` — Add `state` to fields and widgets
- `apps/questions/views.py` — Add state filter to `QuestionListView`
- `apps/questions/templates/questions/question_list.html` — State filter dropdown, checkmark icon, pagination params
- `apps/questions/templates/questions/question_form.html` — State select field
- `apps/questions/templates/questions/question_preview.html` — State badge
- `apps/exams/templates/exams/exam_detail.html` — Checkmark icon
- `apps/exams/templates/exams/pool_template_add.html` — Checkmark icon
- `apps/exams/views.py` — Filter by reviewed state
- `apps/questions/static/questions/js/question_list.js` — Add state select to auto-submit listener
- `apps/questions/tests.py` — Tests for state field, filter, and exam restriction

## Risks / Trade-offs

- **Migration impact:** Existing templates default to `draft`, making them immediately invisible in exam template selection. Users must manually update templates to `reviewed`. This is intentional but should be communicated.
- **No state transition rules:** Any state can be freely set to any other state. This keeps implementation simple but offers no guardrails against accidental state changes.
