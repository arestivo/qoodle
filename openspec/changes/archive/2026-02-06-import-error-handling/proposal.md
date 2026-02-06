## Why

The YAML import command currently:
1. Creates templates without validating they can actually render
2. Creates duplicate templates if run multiple times
3. Ignores the `conditions` field from YAML files

This leads to broken templates in the database and duplicate entries.

## What Changes

Improve the import command with:

1. **Post-import validation**: After creating a template, attempt to render it (generate variables + substitute in text). If it fails, delete the template and report the error.

2. **Skip duplicates**: Before creating a template, check if one with the same title already exists in the Uncategorized subject. If so, skip it.

3. **Import conditions as validation_rules**: Convert the YAML `conditions` array to the model's `validation_rules` field:
   - Strip angle brackets: `<var>` → `var` (be careful not to delete less than and grater than signs)
   - Convert JS equality: `===` → `==`, `!==` → `!=`

## Capabilities

### New Capabilities

_None_

### Modified Capabilities

- **yaml-import-command**: Add validation, duplicate detection, and conditions import

## Impact

- **Low risk**: Import continues to work, just with better error handling
- **No database migration**: Uses existing `validation_rules` field
- **Idempotent imports**: Running import twice won't create duplicates
