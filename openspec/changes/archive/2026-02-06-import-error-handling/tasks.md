# Tasks: Import Error Handling

## Phase 1: Skip Duplicates

- [x] Before creating a template, check if one with the same title exists in Uncategorized subject
- [x] If duplicate found, skip and log "Skipped (duplicate)"
- [x] Add skipped count to stats

## Phase 2: Import Conditions

- [x] Add `convert_conditions()` method to convert YAML conditions to validation_rules
- [x] Convert variable references `<var>` → `var` using regex (preserve `<` and `>` operators)
- [x] Convert `===` → `==` and `!==` → `!=`
- [x] Pass converted conditions to template creation

## Phase 3: Post-Import Validation

- [x] After creating template, attempt to render with seed=0
- [x] If rendering fails, rollback (transaction handles this)
- [x] Log validation errors with filename

## Phase 4: Update Stats

- [x] Add "skipped" count to statistics
- [x] Add "validation_failed" count to statistics (captured by "failed" count)
- [x] Display both in summary
