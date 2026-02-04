# Specification: Subject Hierarchy System

**ID:** subject-hierarchy  
**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** 2026-02-03  
**Change:** hierarchical-subjects (archived)

## Overview

Hierarchical subject organization system allowing tree-based categorization of quiz questions with parent-child relationships.

## Purpose

- Organize questions by academic subject and topic
- Support multi-level hierarchy (e.g., Mathematics → Algebra → Linear Equations)
- Enable subject-based filtering of questions
- Display question counts per subject
- Prevent accidental deletion of subjects with children or questions

## Data Model

### Location
`apps/subjects/models.py`

### Subject Model

```python
class Subject(UUIDModel):
    """Hierarchical subject model for organizing quiz questions."""
    
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                name='unique_subject_name_per_parent'
            )
        ]
```

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | CharField(200) | Subject name | Required, unique per parent level |
| `parent` | ForeignKey(self) | Parent subject | Nullable, PROTECT on delete |
| `description` | TextField | Optional description | Optional |
| `id`, `created_at`, `updated_at` | Inherited | From UUIDModel | - |

### Relationships

| Relationship | Type | Model | On Delete |
|-------------|------|-------|-----------|
| `children` | Reverse FK | Subject | PROTECT |
| `questions` | Reverse FK | Question | PROTECT |

## Business Logic

### Tree Navigation Methods

```python
def get_children(self):
    """Return immediate child subjects."""
    return self.children.all()

def get_ancestors(self):
    """Return all parent subjects up to the root."""
    ancestors = []
    current = self.parent
    while current is not None:
        ancestors.insert(0, current)
        current = current.parent
    return ancestors

def get_descendants(self):
    """Return all child subjects recursively."""
    descendants = []
    for child in self.children.all():
        descendants.append(child)
        descendants.extend(child.get_descendants())
    return descendants

def get_question_count(self) -> int:
    """Return count of questions directly assigned to this subject."""
    return self.questions.count()
```

### Properties

```python
@property
def depth(self) -> int:
    """Return the depth level of this subject in the tree."""
    return len(self.get_ancestors())

@property
def is_root(self) -> bool:
    """Check if this is a root-level subject."""
    return self.parent is None

def has_children(self) -> bool:
    """Check if this subject has any child subjects."""
    return self.children.exists()
```

## URL Patterns

```python
urlpatterns = [
    path('', SubjectListView.as_view(), name='list'),
    path('create/', SubjectCreateView.as_view(), name='create'),
    path('<uuid:pk>/edit/', SubjectUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', SubjectDeleteView.as_view(), name='delete'),
]
```

### Example URLs
- List: `/subjects/`
- Create root: `/subjects/create/`
- Create child: `/subjects/create/?parent=550e8400-e29b-41d4-a716-446655440000`
- Edit: `/subjects/550e8400-e29b-41d4-a716-446655440000/edit/`

## Views

### SubjectListView
- **Template:** `subjects/subject_list.html`
- **Queryset:** Root subjects with `select_related('parent')` and `prefetch_related('children')`
- **Display:** Tree view with indentation, question count badges, action buttons

### SubjectCreateView
- **Template:** `subjects/subject_form.html`
- **Pre-fill:** Parent from `?parent=<uuid>` query parameter
- **Validation:** Unique name per parent level
- **Redirect:** Subject list on success

### SubjectUpdateView
- **Template:** `subjects/subject_form.html`
- **Fields:** name, parent, description
- **Validation:** Cannot set self or descendant as parent (prevents cycles)
- **Redirect:** Subject list on success

### SubjectDeleteView
- **Template:** `subjects/subject_confirm_delete.html`
- **Protection:** Django PROTECT prevents deletion if children or questions exist
- **Display:** Shows count of children and questions
- **Redirect:** Subject list on success

## UI Components

### Subject Tree Display

```django
{% for subject in root_subjects %}
    {% include "subjects/subject_tree_row.html" with subject=subject depth=0 %}
{% endfor %}
```

**Recursive Template** (`subject_tree_row.html`):
- Displays subject with indentation based on depth
- Shows question count as clickable badge linking to filtered questions
- Action buttons: Add Sub-subject, Edit, Delete
- Recursively includes self for each child

### Form Features
- Bootstrap 5.3.8 styled
- Parent selector dropdown
- Description textarea
- Validation error display

## Constraints & Validation

### Database Constraints
1. **Unique Name per Level:** `UniqueConstraint(fields=['parent', 'name'])`
   - Same name allowed at different hierarchy levels
   - Prevents duplicates at same level

2. **Deletion Protection:** `on_delete=PROTECT`
   - Cannot delete subject with children
   - Cannot delete subject with questions
   - Forces user to reassign or delete dependents first

### Application Validation
```python
def clean(self):
    """Prevent circular references and self-parenting."""
    if self.parent == self:
        raise ValidationError("Subject cannot be its own parent")
    
    if self.parent and self in self.parent.get_ancestors():
        raise ValidationError("Circular reference detected")
```

## Testing

### Model Tests
```python
def test_subject_creation()
def test_parent_child_relationship()
def test_unique_constraint_same_parent()
def test_get_ancestors()
def test_get_descendants()
def test_depth_property()
def test_question_count()
def test_cannot_delete_with_children()
def test_cannot_delete_with_questions()
```

### View Tests
```python
def test_list_view_shows_tree()
def test_create_with_parent_prefill()
def test_update_subject()
def test_delete_protected_subject_shows_error()
def test_question_count_display()
```

**Coverage:** 99% (subjects app)

## Performance Considerations

### Queries
- Use `select_related('parent')` for ancestor lookups
- Use `prefetch_related('children')` for tree display
- Annotate with `Count('questions')` for question counts

### Limitations
- No django-mptt: May have performance issues with very deep trees (>10 levels)
- Recursive queries for descendants not optimized
- Consider django-mptt if tree operations become bottleneck

## Admin Interface

```python
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'question_count', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'description']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            question_count=models.Count('questions')
        )
```

## Related Specifications

- [uuid-model-system](../uuid-model-system/spec.md) - Base model
- [multilingual-questions](../multilingual-questions/spec.md) - Uses subjects for organization

## Future Enhancements

- django-mppt integration for better tree performance
- Subject icons/colors
- Subject merging functionality
- Import/export subject hierarchies
- Subject templates for common structures

## References

- Django self-referential ForeignKey: https://docs.djangoproject.com/en/6.0/ref/models/fields/#foreignkey
- Tree structures in Django: https://django-mptt.readthedocs.io/
