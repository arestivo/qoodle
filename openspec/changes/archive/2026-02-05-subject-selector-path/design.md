## Context

The `QuestionTemplateForm` uses Django's default ModelChoiceField for the subject field. The list view already implements full path display and sorting - this pattern should be applied to the form.

## Goals / Non-Goals

**Goals:**
- Show full subject path in the dropdown
- Sort subjects by full path

**Non-Goals:**
- Indentation/tree-style display (just use " > " separator)
- Filtering or searching within the dropdown

## Decisions

### 1. Override label_from_instance

Use a custom ModelChoiceField subclass or override `label_from_instance` to return `subject.get_full_path()`.

**Alternatives considered:**
- Template-based solution: Rejected because Django's select widget doesn't easily support custom option labels

### 2. Sort queryset in form __init__

Sort subjects by computing full paths and using `Case/When` or Python sorting before setting the queryset.

**Alternatives considered:**
- Database-level sorting: Complex for hierarchical data without MPTT/django-treebeard

## Risks / Trade-offs

- **Performance**: Computing paths for all subjects on each form render. Acceptable for typical subject counts (<1000).
