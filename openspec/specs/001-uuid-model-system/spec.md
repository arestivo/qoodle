# Specification: UUID Model System

**ID:** 001-uuid-model-system  
**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** 2026-02-03

## Overview

Abstract base model providing UUID primary keys and automatic timestamp tracking for all database models in the Qoodle application.

## Purpose

- Ensure consistent UUID usage across all models for security and scalability
- Prevent enumeration attacks (non-sequential IDs)
- Provide automatic created/updated timestamp tracking
- Simplify model inheritance and reduce boilerplate

## Implementation

### Location
`apps/common/models.py`

### Model Definition

```python
import uuid
from django.db import models

class UUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUIDField | Primary key | Non-editable, auto-generated UUID4 |
| `created_at` | DateTimeField | Creation timestamp | Auto-set on creation, immutable |
| `updated_at` | DateTimeField | Last modification timestamp | Auto-updated on save |

## Usage

### Extending UUIDModel

All models in the application must extend `UUIDModel`:

```python
from apps.common.models import UUIDModel

class Subject(UUIDModel):
    name = models.CharField(max_length=200)
    # id, created_at, updated_at inherited automatically
```

### URL Patterns

URLs use UUID format:
```python
path('<uuid:pk>/edit/', views.SubjectUpdateView.as_view(), name='edit')
```

Example URLs:
- `/subjects/550e8400-e29b-41d4-a716-446655440000/edit/`
- `/questions/6ba7b810-9dad-11d1-80b4-00c04fd430c8/`

## Benefits

1. **Security**: Non-sequential IDs prevent enumeration attacks
2. **Scalability**: UUIDs can be generated client-side or in distributed systems
3. **Consistency**: All models follow same ID pattern
4. **Auditability**: Automatic timestamp tracking
5. **Django Admin**: UUIDs display nicely in admin interface

## Constraints

1. **Performance**: UUIDs are larger than integers (16 bytes vs 4-8 bytes)
2. **Indexing**: Slightly slower index performance than sequential integers
3. **Database Support**: Requires database with UUID support (PostgreSQL native, SQLite as text)
4. **Immutability**: Primary keys cannot be changed after creation

## Testing

### Test Coverage

```python
def test_uuid_auto_generation():
    """Test that UUID is automatically generated."""
    obj = Subject.objects.create(name="Test")
    assert isinstance(obj.id, uuid.UUID)
    assert obj.id.version == 4

def test_timestamps_auto_set():
    """Test created_at and updated_at are set automatically."""
    obj = Subject.objects.create(name="Test")
    assert obj.created_at is not None
    assert obj.updated_at is not None
    
def test_updated_at_changes():
    """Test updated_at changes on save."""
    obj = Subject.objects.create(name="Test")
    original_updated = obj.updated_at
    obj.name = "Modified"
    obj.save()
    assert obj.updated_at > original_updated
```

## Migration Considerations

### Initial Migration
First migration for any app using UUIDModel:

```python
id = models.UUIDField(
    default=uuid.uuid4,
    editable=False,
    primary_key=True
)
```

### Existing Data Migration
If migrating from integer IDs, requires data migration:
1. Add new UUID field
2. Generate UUIDs for existing records
3. Update foreign key relationships
4. Remove old integer primary key
5. Set UUID as primary key

## Database-Specific Notes

### PostgreSQL
- Native UUID type: `uuid`
- Optimal storage (16 bytes)
- Index performance excellent

### SQLite
- Stored as TEXT (36 characters with hyphens)
- Larger storage overhead
- Adequate for development

## Related Specifications

- [002-subject-hierarchy](../002-subject-hierarchy/spec.md) - Uses UUIDModel
- [003-multilingual-questions](../003-multilingual-questions/spec.md) - Uses UUIDModel

## References

- Django UUIDField: https://docs.djangoproject.com/en/6.0/ref/models/fields/#uuidfield
- UUID RFC 4122: https://datatracker.ietf.org/doc/html/rfc4122
- Python UUID module: https://docs.python.org/3/library/uuid.html
