# Change: Hierarchical Subjects

**Status:** Planning  
**Created:** 2026-02-02  
**Schema:** spec-driven

## Summary

Implement a hierarchical subject management system that allows teachers to organize quiz questions into a tree structure of subjects and sub-subjects. This includes CRUD operations (create, read, update, delete) for subjects with a view showing the number of questions per subject.

## Context

As part of the Qoodle Moodle Quiz Generator, teachers need to organize their questions by subject matter in a hierarchical way (e.g., Mathematics > Algebra > Linear Equations). This foundational feature will enable:

- Better organization of quiz questions
- Easier navigation and question discovery
- Logical grouping for quiz generation

## Goals

1. Create a UUID-based abstract model for all system models
2. Implement hierarchical subject model with self-referential parent relationship
3. Provide full CRUD interface for subject management
4. Display subject hierarchy in a tree-like structure
5. Show question count per subject (placeholder showing 0 for now)

## Non-Goals

- Question management (comes in future iteration)
- Actual question counting logic (will be implemented when questions exist)
- Subject permissions or multi-tenancy
- Subject import/export functionality

## Scope

### In Scope

- `apps/common/models.py` - UUIDModel abstract base class
- `apps/subjects/` - New Django app for subject management
  - Models: Subject with hierarchical relationship
  - Views: List, Create, Edit, Delete
  - Templates: Subject list (tree view), form, delete confirmation
  - URLs: RESTful routing for subject operations
  - Admin: Subject admin configuration
  - Tests: Model tests, view tests, form tests

### Out of Scope

- Question models and relationships
- Subject ordering/reordering functionality
- Bulk operations (bulk delete, bulk move)
- Subject search functionality
- Export to Moodle XML

## Dependencies

- Django 6.0.1 already installed
- Bootstrap 5.3.8 for UI (already configured)
- pytest-django for testing (already configured)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Complex hierarchical queries | Medium | Use Django MPTT or simple parent FK with select_related |
| Orphaned subjects on delete | Medium | Implement cascade delete or reassign to parent |
| Deep nesting performance | Low | Start simple; optimize if needed |

## Success Criteria

- [ ] UUIDModel created and all future models can extend it
- [ ] Subject model with parent relationship works correctly
- [ ] Can create root subjects and nested sub-subjects
- [ ] Can edit subject name and parent
- [ ] Can delete subjects (with appropriate cascade/protection)
- [ ] Subject list displays hierarchical tree structure
- [ ] Question count shows 0 for all subjects
- [ ] All tests pass with >80% coverage
- [ ] Code follows PEP 8 and includes type hints

## Rollback Plan

If issues arise:
1. Remove `apps/subjects` app from INSTALLED_APPS
2. Run `python manage.py migrate subjects zero`
3. Delete `apps/subjects/` directory
4. UUIDModel in common app can remain as it's non-invasive

## Open Questions

- Should we use django-mptt for better hierarchical queries or stick with simple parent FK?
  - **Decision:** Start with simple parent FK, migrate to MPTT if performance becomes an issue
- Should deletion of a parent subject cascade to children or prevent deletion?
  - **Decision:** Prevent deletion if subject has children (protect), require manual cleanup
