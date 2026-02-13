## Implementation Tasks

- [x] Create `apps/data` app scaffold: `apps/data/__init__.py`, `apps/data/apps.py` (with `DataConfig`), `apps/data/management/__init__.py`, `apps/data/management/commands/__init__.py`
- [x] Register `"apps.data"` in `INSTALLED_APPS` in `qoodle/settings.py`
- [x] Implement `export_data()` and helper serialization functions in `apps/data/services.py` (subjects in topological order, templates, choices, exams, pools, pool-templates; UUID/datetime/JSON fields properly serialized)
- [x] Implement `get_existing_data_counts()` and `delete_all_data()` in `apps/data/services.py`
- [x] Implement `import_data(data)` in `apps/data/services.py` (create records in dependency order: subjects parents-first, templates, choices, exams, pools, pool-templates; preserve UUIDs)
- [x] Create `export_data` management command in `apps/data/management/commands/export_data.py` (positional `output_path` arg, calls `services.export_data()`, writes JSON with indent=2, prints counts)
- [x] Create `import_data` management command in `apps/data/management/commands/import_data.py` (positional `input_path` arg, `--force` flag, non-empty DB warning, atomic transaction wrapping `delete_all_data()` + `import_data()`)
- [x] Add URL routing: create `apps/data/urls.py` with `app_name = "data"` and paths for index, export, import; add `path("data/", include("apps.data.urls"))` to `qoodle/urls.py`
- [x] Implement `DataIndexView` in `apps/data/views.py` (TemplateView rendering `apps/data/templates/data/index.html` with export/import cards)
- [x] Implement `export_view` in `apps/data/views.py` (GET returns JSON file download with `Content-Disposition: attachment; filename=qoodle-export-YYYY-MM-DD.json`)
- [x] Implement `import_view` in `apps/data/views.py` (POST handles file upload; if DB non-empty, store parsed data in session and render `apps/data/templates/data/import_confirm.html`; if empty or confirmed, run atomic import and redirect with success message)
- [x] Create `apps/data/templates/data/index.html` extending `common/base.html` (export card with download button, import card with file upload form)
- [x] Create `apps/data/templates/data/import_confirm.html` extending `common/base.html` (warning with existing record counts, confirm/cancel buttons, hidden `confirm=true` field)
- [x] Add "Data" nav link with `fa-solid fa-database` icon to `apps/common/templates/common/base.html` after the Exams link
- [x] Add tests in `apps/data/tests.py`: export round-trip (export then import produces same data), export empty DB, import into empty DB, import into non-empty DB without force (command exits), import with force, import invalid JSON, import preserves UUIDs, web export download, web import with confirmation flow
- [x] Run tests: `poetry run python manage.py test apps.data`
