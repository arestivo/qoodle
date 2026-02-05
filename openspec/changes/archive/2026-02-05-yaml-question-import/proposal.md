## Why

Questions are currently created manually through the web interface, which is time-consuming for bulk imports. An existing collection of questions exists in YAML format with separate English and Portuguese files, and we need to import them into Qoodle efficiently.

The YAML files use a different syntax for variables (`<var>` instead of `{{var}}`) and structure (`values` instead of `items` for sets), so conversion is required during import.

## What Changes

A new Django management command `import_yaml_questions` will be created to:

1. Read YAML question files from a specified folder with `en/` and `pt/` subdirectories
2. Convert variable syntax from YAML format to model format
3. Detect multilingual vs language-independent text by comparing English and Portuguese versions
4. Create `QuestionTemplate` and `Choice` records in the database

## Capabilities

### New Capabilities

- **yaml-import-command**: Management command to import questions from YAML files with automatic variable conversion and multilingual text detection

### Modified Capabilities

_None - this is a new standalone feature_

## Impact

- **Low risk**: This is an additive feature that creates new database records without modifying existing ones
- **Subject dependency**: Questions are assigned to an "Uncategorized" root-level Subject (created if needed)
- **No new dependencies**: Uses only standard library (`yaml` is already available via PyYAML in Django ecosystem)
- **Reversible**: Imported questions can be deleted through the admin interface if needed
