## Context

An existing collection of questions exists in YAML format with English and Portuguese versions in separate folders. These need to be imported into Qoodle's existing `QuestionTemplate` and `Choice` models. The YAML format uses different syntax conventions that require conversion during import.

## Goals / Non-Goals

**Goals:**
- Import questions from YAML files into the database via a Django management command
- Convert YAML variable syntax (`values` → `items`, `<var>` → `{{var}}`)
- Detect and handle multilingual vs language-independent text automatically
- Provide comprehensive error reporting without stopping on individual failures

**Non-Goals:**
- No web interface for importing (management command only)
- No support for single-language YAML files (requires both en/pt)
- No modification of existing questions (import only creates new records)
- No export functionality (one-way import)

## Decisions

### 1. No Database Schema Changes

Use the existing `QuestionTemplate` and `Choice` models without modification. The current models already support:
- Multilingual text via JSONField with `{"en": ..., "pt": ...}` or `{"none": ...}` format
- Variables via JSONField with `type`, `items`, `min`, `max`, `formula` fields
- Choices linked to templates with `order` field (0 = correct answer)

**Alternatives considered:**
- Adding import metadata fields (imported_from, import_date): Rejected as unnecessary complexity; the existing `created_at` timestamp is sufficient

### 2. Management Command Location

Place the command at `apps/questions/management/commands/import_yaml_questions.py`.

**Alternatives considered:**
- Creating a new `apps/importer/` app: Rejected because import is tightly coupled to the questions app and doesn't warrant a separate app

### 3. Variable Conversion Strategy

Perform in-memory conversion during parsing:
1. **Key renaming**: `values` → `items` for set-type variables
2. **Reference syntax**: Regex replacement `<(\w+(?:\[\d+\])?)>` → `{{$1}}`

The conversion happens before database insertion, so stored data matches the expected model format.

**Alternatives considered:**
- Storing original YAML format and converting at render time: Rejected because it would require changes to the existing rendering pipeline

### 4. Multilingual Text Detection

Compare English and Portuguese text after variable reference conversion:
- If `en_text == pt_text`: Store as `{"none": text}` (language-independent)
- If `en_text != pt_text`: Store as `{"en": en_text, "pt": pt_text}`

Apply this logic independently to:
- Question text
- Each choice text (choices may mix language-independent and language-specific)

**Alternatives considered:**
- Always storing both languages: Rejected because language-independent text (e.g., mathematical expressions) should use `none` key per existing model conventions

### 5. Title Derivation from Filename

Convert filename to title using:
1. Remove extension (`.yaml` or `.yml`)
2. Replace hyphens/underscores with spaces
3. Apply title case

Example: `spa-advantage.yaml` → `Spa Advantage`

**Alternatives considered:**
- Reading title from YAML content: Rejected because the existing YAML format doesn't include a title field

### 6. Error Handling Approach

Continue processing on individual file failures:
- Log errors with filename context
- Track success/failure counts
- Report comprehensive summary at end

This allows batch imports to complete even if some files have issues.

**Alternatives considered:**
- Fail-fast on first error: Rejected because partial imports are useful when dealing with large question banks
- Database transactions per file: Will use, so failed files don't leave partial data

### 7. Subject Assignment

All imported questions are assigned to an "Uncategorized" root-level Subject:
- Created automatically if it doesn't exist (using `get_or_create`)
- Users can manually reorganize questions after import via the web interface

**Alternatives considered:**
- Accepting subject as command argument: Rejected as over-engineering for initial implementation; can be added later if needed

## Risks / Trade-offs

1. **Duplicate imports**: No deduplication logic; running the command twice creates duplicate questions. Mitigation: Document this behavior and recommend clearing imported questions before re-importing.

2. **YAML format assumptions**: The command assumes a specific YAML structure. Mitigation: Provide clear error messages when format doesn't match expectations.

3. **Expression formula compatibility**: YAML formulas must be valid Python expressions compatible with the existing `evaluate_expression` function. Mitigation: Log validation errors during import.

4. **Missing PyYAML dependency**: The command requires PyYAML. Mitigation: PyYAML is typically included with Django projects; add to dependencies if missing.
