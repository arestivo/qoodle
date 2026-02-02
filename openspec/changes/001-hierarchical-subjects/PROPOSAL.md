# Proposal: Hierarchical Subjects

## Problem Statement

Qoodle needs a way to organize quiz questions hierarchically by subject matter. Teachers must be able to:
- Create subjects and sub-subjects in a tree structure
- Navigate through subject hierarchies
- See at a glance how many questions belong to each subject
- Manage (create, edit, delete) subjects efficiently

Currently, there is no subject model or organizational structure in the system.

## Proposed Solution

### 1. Create UUID Abstract Base Model

Create a reusable `UUIDModel` abstract base class in `apps/common/models.py` that all models in the system will extend. This ensures:
- Consistent UUID primary keys across all models
- No sequential ID exposure
- Better security and less predictable URLs

```python
class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

### 2. Create Subjects Django App

Create a new Django app `apps/subjects/` with:

**Model: Subject**
- Extends `UUIDModel`
- Fields:
  - `name` - CharField(max_length=200)
  - `parent` - ForeignKey to self (nullable, for hierarchy)
  - `description` - TextField (optional)
- Methods:
  - `get_children()` - Returns immediate child subjects
  - `get_ancestors()` - Returns all parent subjects up to root
  - `get_descendants()` - Returns all child subjects recursively
  - `question_count` - Property returning 0 (placeholder)
- Meta:
  - Ordering by name
  - Unique constraint on (parent, name) to prevent duplicate names at same level

**Views**
- `SubjectListView` - Display hierarchical tree of all subjects
- `SubjectCreateView` - Form to create new subject with optional parent
- `SubjectUpdateView` - Form to edit subject name, description, parent
- `SubjectDeleteView` - Delete confirmation with cascade warning

**Templates**
- `subjects/subject_list.html` - Tree view with indentation showing hierarchy
- `subjects/subject_form.html` - Create/edit form
- `subjects/subject_confirm_delete.html` - Delete confirmation

**URLs**
```
/subjects/ - List all subjects
/subjects/create/ - Create new subject
/subjects/<uuid:pk>/edit/ - Edit subject
/subjects/<uuid:pk>/delete/ - Delete subject
```

### 3. Admin Configuration

Register Subject model in Django admin with:
- List display: name, parent, question_count
- List filter: parent (root vs sub-subjects)
- Search: name, description
- Tree hierarchy visualization if possible

### 4. Testing Strategy

- **Model Tests**:
  - UUID generation
  - Hierarchical relationships (parent/children)
  - Cascade behavior on delete
  - Unique constraint validation
  
- **View Tests**:
  - List view displays hierarchy correctly
  - Create subject (root and nested)
  - Edit subject (change name, change parent)
  - Delete subject (with and without children)
  - Permission checks (will use Django's built-in for now)

- **Integration Tests**:
  - Full CRUD workflow
  - Tree integrity after operations

## Alternatives Considered

### Alternative 1: Use django-mptt
**Pros:** Optimized tree queries, better performance for large trees  
**Cons:** Additional dependency, more complex migrations, overkill for initial version  
**Decision:** Rejected for v1, can migrate later if needed

### Alternative 2: Use django-treebeard
**Pros:** Multiple tree algorithms, well-maintained  
**Cons:** Additional dependency, learning curve  
**Decision:** Rejected for same reasons as MPTT

### Alternative 3: Flat structure with tags
**Pros:** Simpler model  
**Cons:** Doesn't meet requirement for hierarchical organization  
**Decision:** Rejected - hierarchy is a core requirement

## Implementation Plan

### Phase 1: Foundation (UUIDModel)
1. Create `UUIDModel` in `apps/common/models.py`
2. Write tests for UUIDModel
3. Document usage in docstrings

### Phase 2: Subject Model & Admin
1. Create `apps/subjects/` app
2. Implement `Subject` model
3. Create and run migrations
4. Configure Django admin
5. Write model tests

### Phase 3: Views & Templates
1. Implement SubjectListView with tree rendering
2. Implement SubjectCreateView
3. Implement SubjectUpdateView
4. Implement SubjectDeleteView
5. Create templates using Bootstrap
6. Write view tests

### Phase 4: Integration & Polish
1. Add URL configuration
2. Update navigation in base template
3. Run full test suite
4. Code review and cleanup
5. Update documentation

## Success Metrics

- All tests pass with >80% coverage
- Can create 3-level deep subject hierarchy
- UI is responsive and intuitive
- No performance issues with 100+ subjects
- Code passes black, ruff, mypy checks

## Timeline Estimate

- Phase 1: 30 minutes
- Phase 2: 1 hour
- Phase 3: 2 hours
- Phase 4: 30 minutes

**Total:** ~4 hours

## Future Enhancements

- Drag-and-drop reordering of subjects
- Bulk operations (move, delete)
- Subject icons/colors
- Import/export subject trees
- Subject-level permissions
- Integration with django-mptt when tree grows large
