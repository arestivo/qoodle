## MODIFIED Requirements

### Requirement: Post-Import Validation

After creating a template, validate it can render successfully.

#### Scenario: Template renders successfully
- **WHEN** a template is created
- **THEN** attempt to generate variables and render text
- **THEN** if successful, keep the template

#### Scenario: Template fails to render
- **WHEN** a template is created but fails to render
- **THEN** delete the template
- **THEN** log error: "Failed to validate: filename.yaml - [error details]"
- **THEN** increment failed count

---

### Requirement: Skip Duplicate Templates

Before creating a template, check for existing duplicates.

#### Scenario: Template with same title exists
- **WHEN** importing a template
- **AND** a template with the same title exists in Uncategorized subject
- **THEN** skip the template
- **THEN** log: "Skipped (duplicate): filename.yaml"

#### Scenario: Template with same title in different subject
- **WHEN** a template with the same title exists in a different subject
- **THEN** proceed with import (not a duplicate)

---

### Requirement: Import Conditions as Validation Rules

Convert YAML conditions to model validation_rules.

#### Scenario: Conditions with variable references
- **WHEN** YAML contains `conditions: ["<r> > 0"]`
- **THEN** convert to `validation_rules: ["r > 0"]`
- **THEN** variable references `<var>` become `var`

#### Scenario: JavaScript equality operators
- **WHEN** YAML contains `conditions: ["<x> === 5"]`
- **THEN** convert to `validation_rules: ["x == 5"]`
- **THEN** `===` becomes `==`, `!==` becomes `!=`

#### Scenario: Preserve comparison operators
- **WHEN** YAML contains `conditions: ["<a> > <b>", "<x> < 10"]`
- **THEN** `>` and `<` comparison operators are preserved
- **THEN** only `<var>` patterns are converted
