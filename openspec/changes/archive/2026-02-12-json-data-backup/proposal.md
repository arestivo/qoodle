## Why

There is currently no way to back up the full application state or transfer data between instances. The only import path is the YAML question importer, which handles a specific external format and only covers questions (not exams). A JSON export/import feature would allow users to save a complete snapshot of their data and restore it on another instance or after a database reset.

## What Changes

Add both a web interface and management commands for full data export/import:

**Web Interface:**
- A new "Data" section in the navigation with export and import pages
- Export page with a download button that streams a JSON file
- Import page with a file upload form. If the database already contains application data, a warning is shown and the user must confirm before proceeding. The import deletes all existing application data and replaces it with the uploaded file's content.

**Management Commands:**
- **`export_data`** — Serializes all application models (subjects, templates, choices, exams, pools, pool-templates) to a JSON file written to the specified path.
- **`import_data`** — Reads a JSON file and populates the database. If the database already contains application data, the command warns and requires `--force` to proceed.

Only application ("nuclear") data is exported/imported. Django system tables (auth, sessions, content types, migrations, etc.) are not touched.

## Capabilities

### New Capabilities

- **json-data-export**: Export all application data to a JSON file (web UI download + management command)
- **json-data-import**: Import a JSON file with destructive-replace semantics and safety confirmation (web UI upload + management command)

### Modified Capabilities

None — this is additive functionality with no changes to existing features.

## Impact

- **New app or views needed** for the web interface (export download endpoint, import upload page).
- **No changes to existing models.** Export/import logic is standalone.
- **Shared core logic:** The serialization/deserialization code is implemented once in a service module. Both management commands and web views call the same functions — no duplication.
- **Destructive import by design:** Importing into a non-empty database deletes all application data first. This is intentional — the feature targets full backup/restore, not incremental merge.
- **UUID preservation:** Exported UUIDs are preserved on import, so references remain stable across export/import cycles.
