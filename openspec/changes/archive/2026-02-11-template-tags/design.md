## Context

Templates are organized by subject hierarchy but lack cross-cutting labels. This change adds a simple comma-separated tags field to `QuestionTemplate`, displayed as badges in listing views and editable through the existing form.

## Goals / Non-Goals

**Goals:**
- Store tags as a comma-separated string on each template
- Display tags as `badge bg-secondary` in a `d-flex gap-1` container in both listing views
- Allow editing tags via the existing question create/edit form

**Non-Goals:**
- Tag-based filtering or search
- Tag autocomplete or suggestions
- Separate Tag model or many-to-many relationship

## Decisions

### 1. Comma-separated CharField over M2M Tag model

Use `CharField(max_length=500, blank=True, default="")` on `QuestionTemplate` rather than a separate `Tag` model with M2M relationship.

A helper method `tag_list() -> list[str]` splits, strips, and filters empty strings.

**Alternatives considered:**
- Separate `Tag` model with M2M: Rejected — overkill for display-only labels with no filtering needs. Adds migration complexity and extra queries.
- `JSONField` with list: Rejected — less user-friendly for form input, no advantage over comma-separated for this use case.

### 2. Database schema change

**Model:** `QuestionTemplate` in `apps/questions/models.py`

**New field:**
```python
tags = models.CharField(max_length=500, blank=True, default="")
```

**New method:**
```python
def tag_list(self) -> list[str]:
    return [t.strip() for t in self.tags.split(",") if t.strip()]
```

**Migration:** Single `AddField` migration in `apps/questions/migrations/`. Non-destructive — blank/default means no data loss.

### 3. Form integration

Add `tags` to the `QuestionForm.Meta.fields` list (after `subject`). Use a standard `CharField` with `TextInput` widget — no custom field needed since tags are stored as a plain string.

**Field definition in Meta.widgets:**
```python
"tags": forms.TextInput(attrs={
    "class": "form-control",
    "placeholder": "easy, exam-2024, review",
})
```

**Help text:** `"Comma-separated tags (e.g. easy, exam-2024, review)"`

**Field ordering:** `["title", "subject", "tags", "text", "variables_json", "validation_rules_json"]`

### 4. Template rendering — question list

**File:** `apps/questions/templates/questions/question_list.html`

In the title cell of the template table, after the title link, render tag badges using `tag_list`:

```html
{% if question.tag_list %}
<div class="d-flex gap-1">
  {% for tag in question.tag_list %}
    <span class="badge bg-secondary">{{ tag }}</span>
  {% endfor %}
</div>
{% endif %}
```

No new table column — badges appear below/next to the title within the existing cell.

### 5. Template rendering — pool template add

**File:** `apps/exams/templates/exams/pool_template_add.html`

In each template entry, after the existing variable badges, render tag badges:

```html
{% if template.tag_list %}
<div class="d-flex gap-1">
  {% for tag in template.tag_list %}
    <span class="badge bg-secondary">{{ tag }}</span>
  {% endfor %}
</div>
{% endif %}
```

### 6. No URL routing changes

No new URL patterns needed. Tags are edited through the existing create/edit views and displayed in existing list views.

### 7. No new template tags or filters

`tag_list()` is a model method callable directly in templates (e.g., `question.tag_list`). No custom template tags or filters required.

### 8. No static file changes

No new CSS or JS needed — uses existing Bootstrap `badge`, `d-flex`, and `gap-1` utility classes.

## Risks / Trade-offs

- **500 char limit:** Sufficient for typical use (~25 tags at 20 chars each). If exceeded, tags would be silently truncated by the database. Acceptable for current scope.
- **No normalization on save:** Tags are stored as entered (with user-provided casing). `tag_list()` only strips whitespace. Consistent tagging relies on user discipline.
- **No index on tags field:** Comma-separated storage doesn't support efficient `WHERE` queries. Acceptable since filtering is a non-goal.
