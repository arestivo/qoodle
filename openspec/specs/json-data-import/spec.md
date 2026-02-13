## ADDED Requirements

### Requirement: Import application data from JSON with destructive replace

A JSON import feature that reads an exported JSON file and populates the database. If existing application data is present, the user is warned and must confirm before all existing data is deleted and replaced. Available through both a web UI upload form and a management command.

#### Scenario: Import into empty database via web UI
- **GIVEN** the database has no application data
- **WHEN** the user uploads a valid JSON file on the import page
- **THEN** all data from the file is imported
- **AND** a success message shows the count of imported records per model type
- **AND** the user is redirected to the data management page

#### Scenario: Import into non-empty database via web UI — warning shown
- **GIVEN** the database already contains application data
- **WHEN** the user uploads a JSON file on the import page
- **THEN** a confirmation page is shown warning that all existing data will be deleted
- **AND** the warning shows counts of existing records that will be deleted
- **AND** the user must click "Confirm Import" to proceed or "Cancel" to abort

#### Scenario: Import into non-empty database — confirmed
- **GIVEN** the user has confirmed the destructive import
- **WHEN** the import proceeds
- **THEN** all existing application data (subjects, templates, choices, exams, pools, pool-templates) is deleted
- **AND** the JSON file data is imported
- **AND** the entire operation runs inside a database transaction (atomic)

#### Scenario: Import into empty database via management command
- **GIVEN** the database has no application data
- **WHEN** the user runs `poetry run python manage.py import_data backup.json`
- **THEN** all data is imported and a summary is printed

#### Scenario: Import into non-empty database via management command — no force flag
- **GIVEN** the database contains application data
- **WHEN** the user runs `poetry run python manage.py import_data backup.json` (without `--force`)
- **THEN** the command prints a warning showing existing record counts
- **AND** the command exits without modifying the database

#### Scenario: Import into non-empty database via management command — with force flag
- **GIVEN** the database contains application data
- **WHEN** the user runs `poetry run python manage.py import_data backup.json --force`
- **THEN** all existing application data is deleted and replaced with the file contents

#### Scenario: Import with invalid JSON
- **GIVEN** a malformed or invalid JSON file
- **WHEN** the import is attempted
- **THEN** an error message is shown (web UI) or printed (command)
- **AND** the database is not modified

#### Scenario: Import with missing version field
- **GIVEN** a JSON file without the `version` field
- **WHEN** the import is attempted
- **THEN** an error is raised indicating an unsupported or missing format version

#### Scenario: Import preserves UUIDs
- **GIVEN** a valid JSON export file with UUID primary keys
- **WHEN** the data is imported
- **THEN** all records are created with their original UUIDs
- **AND** ForeignKey relationships are correctly resolved

#### Scenario: Import order respects dependencies
- **GIVEN** a valid JSON file
- **WHEN** data is imported
- **THEN** records are created in dependency order: subjects first (parents before children), then templates, choices, exams, pools, pool-templates

### Web UI

- **URL:** `GET /data/import/` — shows upload form
- **URL:** `POST /data/import/` — handles file upload
- **Template:** `apps/data/templates/data/import.html` — Bootstrap 5 file upload form with drag-and-drop styling
- **Confirmation:** If the database is non-empty, the POST returns a confirmation page. A second POST with a hidden `confirm=true` field performs the actual import.

### Management Command

- **Command:** `import_data <input_path>`
- **Arguments:** `input_path` — file path to read the JSON from
- **Options:** `--force` — skip the non-empty database warning and proceed with destructive import
- **Output:** Prints count of imported records per model type, or warning if database is non-empty and `--force` not set

### Data Integrity

- The entire import (delete + create) is wrapped in `transaction.atomic()`
- If any error occurs during import, the transaction rolls back and no data is modified
- Subject parent-child relationships are resolved by importing root subjects first, then children (topological order)
