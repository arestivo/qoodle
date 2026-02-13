## ADDED Requirements

### Requirement: Export all application data to JSON

A JSON export feature that serializes all application models into a single downloadable file. Available through both a web UI endpoint and a management command.

The exported models (in dependency order): Subject, QuestionTemplate, Choice, Exam, QuestionPool, QuestionPoolTemplate.

The JSON structure uses a top-level object with a key per model type, each containing an array of serialized records. UUIDs, JSONField content (multilingual text, variables, validation rules), timestamps, and ordering fields are all preserved.

#### Scenario: Export via web UI download
- **GIVEN** the database contains subjects, templates, choices, and exams
- **WHEN** the user visits the data management page and clicks the export button
- **THEN** a JSON file is downloaded with filename `qoodle-export-YYYY-MM-DD.json`
- **AND** the response has `Content-Type: application/json` and `Content-Disposition: attachment`

#### Scenario: Export via management command
- **GIVEN** the database contains application data
- **WHEN** the user runs `poetry run python manage.py export_data output.json`
- **THEN** a JSON file is written to `output.json` containing all application data
- **AND** the command prints a summary of exported record counts

#### Scenario: Export from empty database
- **GIVEN** the database has no application data
- **WHEN** the export is triggered (web UI or command)
- **THEN** a valid JSON file is produced with empty arrays for each model type

#### Scenario: JSON structure
- **GIVEN** the database contains data
- **WHEN** the export is generated
- **THEN** the JSON has this top-level structure:
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
- **AND** each record includes its UUID `id` field and all model fields
- **AND** ForeignKey fields are serialized as UUID strings
- **AND** JSONField values (text, variables, validation_rules) are serialized as nested JSON objects/arrays

#### Scenario: Export preserves hierarchical subject references
- **GIVEN** subjects with parent-child relationships exist
- **WHEN** the export is generated
- **THEN** each subject record includes a `parent` field with the parent's UUID (or `null` for root subjects)

### Web UI Endpoint

- **URL:** `GET /data/export/`
- **View:** Returns a `JsonResponse` or `StreamingHttpResponse` with the exported JSON
- **Template:** No template needed — direct file download

### Management Command

- **Command:** `export_data <output_path>`
- **Arguments:** `output_path` — file path to write the JSON to
- **Options:** None
- **Output:** Prints count of exported records per model type

### Navigation

- Add a "Data" link to the main navigation bar pointing to the data management page (`/data/`)
- The data management page shows both export and import actions
