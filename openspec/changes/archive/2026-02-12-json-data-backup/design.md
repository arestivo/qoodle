## Context

The project has four Django apps (`common`, `subjects`, `questions`, `exams`) with six application models that use UUID primary keys via `UUIDModel`. There is no existing backup/restore mechanism. The existing YAML importer only covers questions and uses a different format. This design adds a new `data` app with shared service functions for export/import, consumed by both web views and management commands.

## Goals / Non-Goals

**Goals:**
- Export all application data to a single JSON file (web download + management command)
- Import a JSON file with full destructive replace (web upload + management command)
- Warn users before destructive import on non-empty databases
- Share all serialization/deserialization logic between web and CLI interfaces
- Preserve UUIDs and all relationships across export/import cycles

**Non-Goals:**
- Incremental or merge-based import (always full replace)
- Streaming export for very large datasets (entire payload fits in memory)
- Schema migration between format versions (version field reserved for future use)
- Authentication or permission checks (no auth system in the project)

## Decisions

### 1. New `apps/data` Django app

Create a new `apps.data` app to house the export/import functionality. This keeps the feature isolated from existing apps and follows the project convention of one concern per app.

The app contains:
- `apps/data/services.py` — shared export/import logic
- `apps/data/views.py` — web UI views
- `apps/data/urls.py` — URL routing
- `apps/data/templates/data/` — templates
- `apps/data/management/commands/export_data.py`
- `apps/data/management/commands/import_data.py`
- `apps/data/tests.py` — tests

Register as `"apps.data"` in `INSTALLED_APPS`.

**Alternatives considered:**
- Putting commands in `apps/questions/management/`: Rejected — this feature spans all apps, not just questions.

### 2. Shared service module (`apps/data/services.py`)

Two main functions:

```python
def export_data() -> dict:
    """Serialize all application data to a dictionary."""

def import_data(data: dict) -> dict:
    """Import data from a dictionary. Returns counts of imported records.
    Caller is responsible for wrapping in transaction.atomic() and
    deleting existing data before calling this."""
```

Helper functions:

```python
def get_existing_data_counts() -> dict:
    """Return counts of existing records per model type."""

def delete_all_data() -> None:
    """Delete all application data in correct order (reverse dependency)."""
```

Both the management commands and web views call these functions. The service module handles serialization/deserialization but does not handle I/O (file writing, HTTP responses) or user confirmation — that's the caller's job.

**Alternatives considered:**
- Django's built-in `dumpdata`/`loaddata`: Rejected — includes Django internal tables, uses Django's serialization format which is harder to read, and doesn't support the confirmation/warning flow.

### 3. JSON format (version 1)

Top-level structure with a `version` field for future-proofing:

```json
{
  "version": 1,
  "exported_at": "2026-02-11T12:00:00Z",
  "subjects": [...],
  "templates": [...],
  "choices": [...],
  "exams": [...],
  "pools": [...],
  "pool_templates": [...]
}
```

Each record is a flat dictionary with all model fields. UUIDs are serialized as strings. JSONField values are nested directly (not double-encoded). DateTimeField values use ISO 8601 format. DateField values use `YYYY-MM-DD` or `null`.

Example subject record:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mathematics",
  "description": "Math questions",
  "parent": null,
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

### 4. Export serialization approach

Use manual serialization (model-to-dict) rather than Django REST Framework or `django.core.serializers`. Each model type has a straightforward field list and the manual approach keeps it simple with no new dependencies.

Subjects are exported in topological order (parents before children) to make the file human-readable and simplify import.

### 5. Import deserialization and ordering

Import creates records in dependency order:
1. **Subjects** — root subjects first, then children (topological sort by `parent`)
2. **QuestionTemplates** — depend on Subject FK
3. **Choices** — depend on QuestionTemplate FK
4. **Exams** — no FK dependencies on above
5. **QuestionPools** — depend on Exam FK
6. **QuestionPoolTemplates** — depend on QuestionPool and QuestionTemplate FKs

Delete order is the reverse: pool-templates, pools, exams, choices, templates, subjects.

UUID primary keys from the export are preserved on import using `Model.objects.create(id=uuid, ...)`.

### 6. Web UI — data management page

A single page at `/data/` with two cards: Export and Import.

**Export card:** A button that triggers a GET to `/data/export/` which returns the JSON file as a download.

**Import card:** A file upload form (`enctype="multipart/form-data"`) that POSTs to `/data/import/`. If the database is non-empty, the view stores the uploaded file content in the session and renders a confirmation page showing what will be deleted. The confirmation form POSTs again with `confirm=true` to execute the import.

**Templates:**
- `apps/data/templates/data/index.html` — main page with export/import cards
- `apps/data/templates/data/import_confirm.html` — confirmation page for non-empty DB

All templates extend `common/base.html`.

### 7. URL routing

```python
# apps/data/urls.py
app_name = "data"
urlpatterns = [
    path("", DataIndexView.as_view(), name="index"),
    path("export/", export_view, name="export"),
    path("import/", import_view, name="import"),
]
```

Add to `qoodle/urls.py`:
```python
path("data/", include("apps.data.urls")),
```

### 8. Navigation

Add a "Data" nav link in `apps/common/templates/common/base.html` after the Exams link:

```html
<li class="nav-item">
    <a class="nav-link" href="{% url 'data:index' %}">
        <i class="fa-solid fa-database"></i> Data
    </a>
</li>
```

### 9. Management commands

**`export_data`:**
- Takes one positional argument: `output_path`
- Calls `services.export_data()`, writes JSON to file with `json.dump(..., indent=2)`
- Prints record counts to stdout

**`import_data`:**
- Takes one positional argument: `input_path`
- Optional `--force` flag
- Reads JSON from file
- Calls `services.get_existing_data_counts()` to check if DB is non-empty
- If non-empty and no `--force`: prints warning with counts, exits
- If empty or `--force`: wraps `services.delete_all_data()` + `services.import_data()` in `transaction.atomic()`, prints summary

### 10. Template inheritance

- `apps/data/templates/data/index.html` extends `common/base.html`
- `apps/data/templates/data/import_confirm.html` extends `common/base.html`

No new template tags or filters needed. Uses Django's `messages` framework for success/error feedback after import.

### 11. Static files

No new static files needed. The data management page uses standard Bootstrap 5 components (cards, buttons, file input, alerts). No custom CSS or JavaScript required.

## Files Modified

- `qoodle/settings.py` — Add `"apps.data"` to `INSTALLED_APPS`
- `qoodle/urls.py` — Add `path("data/", include("apps.data.urls"))`
- `apps/common/templates/common/base.html` — Add "Data" nav link

## Files Created

- `apps/data/__init__.py`
- `apps/data/apps.py`
- `apps/data/services.py` — shared export/import logic
- `apps/data/views.py` — web UI views
- `apps/data/urls.py` — URL patterns
- `apps/data/templates/data/index.html` — main data management page
- `apps/data/templates/data/import_confirm.html` — import confirmation page
- `apps/data/management/__init__.py`
- `apps/data/management/commands/__init__.py`
- `apps/data/management/commands/export_data.py`
- `apps/data/management/commands/import_data.py`
- `apps/data/tests.py`

## Risks / Trade-offs

- **Full in-memory export:** The entire dataset is serialized to a dict before writing. For very large databases this could use significant memory. Acceptable for the expected scale of this project.
- **Session storage for confirmation:** The uploaded file is stored in the Django session between the upload and confirmation steps. Large files could exceed session backend limits. Mitigation: the session stores the parsed dict, not raw file bytes, and typical backups are well within limits.
- **No schema versioning logic yet:** The `version: 1` field is included but there's no migration path for future format changes. This is intentional — kept simple until a second version is needed.
- **Destructive-only import:** There is no merge mode. Users who want to combine data from two instances cannot do so through this feature. This matches the stated non-goal.
