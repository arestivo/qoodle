## ADDED Requirements

### Requirement: Management Command Interface

The command accepts a folder path argument and validates the folder structure before processing.

#### Scenario: Valid folder with en/pt subdirectories
- **WHEN** running `poetry run python manage.py import_yaml_questions /path/to/questions`
- **THEN** the command validates that `/path/to/questions/en/` and `/path/to/questions/pt/` exist
- **THEN** processing begins

#### Scenario: Missing folder
- **WHEN** the specified folder does not exist
- **THEN** the command exits with error: "Folder not found: /path/to/questions"

#### Scenario: Missing language subdirectory
- **WHEN** the folder exists but `en/` or `pt/` subdirectory is missing
- **THEN** the command exits with error: "Missing required subdirectory: en" or "pt"

---

### Requirement: YAML File Discovery and Pairing

The command finds all YAML files in both language folders and validates they have matching pairs.

#### Scenario: Matching YAML files
- **WHEN** `en/question1.yaml` exists
- **THEN** the command expects `pt/question1.yaml` to also exist
- **THEN** both files are processed as a pair

#### Scenario: Orphan file in English folder
- **WHEN** `en/question2.yaml` exists but `pt/question2.yaml` does not
- **THEN** the file is skipped with warning: "No Portuguese translation for: question2.yaml"

#### Scenario: File extensions
- **WHEN** discovering files
- **THEN** both `.yaml` and `.yml` extensions are accepted

---

### Requirement: Variable Syntax Conversion

Variables in YAML format are converted to the model's expected format.

#### Scenario: Set variable conversion
- **WHEN** YAML contains `vars: { c: { type: set, values: ['A', 'B'], size: 1 } }`
- **THEN** convert to `{ "c": { "type": "set", "items": ["A", "B"], "size": 1 } }`
- **THEN** `values` key becomes `items`

#### Scenario: Numeric variable passthrough
- **WHEN** YAML contains `vars: { x: { type: num, min: 1, max: 10, precision: 0.5 } }`
- **THEN** convert to `{ "x": { "type": "num", "min": 1, "max": 10, "precision": 0.5 } }`

#### Scenario: Expression variable passthrough
- **WHEN** YAML contains `vars: { sum: { type: expression, formula: "a + b" } }`
- **THEN** convert to `{ "sum": { "type": "expression", "formula": "a + b" } }`

---

### Requirement: Text Variable Reference Conversion

Variable references in question and choice text are converted from angle bracket to double brace syntax.

#### Scenario: Simple variable reference
- **WHEN** text contains `<x>`
- **THEN** convert to `{{x}}`

#### Scenario: Array index reference
- **WHEN** text contains `<c[0]>`
- **THEN** convert to `{{c[0]}}`

#### Scenario: Multiple references in text
- **WHEN** text contains `The sum of <a> and <b> is <sum>`
- **THEN** convert to `The sum of {{a}} and {{b}} is {{sum}}`

---

### Requirement: Multilingual Text Detection

Text fields are compared between English and Portuguese to determine if they should be language-independent or language-specific.

#### Scenario: Identical text in both languages
- **WHEN** English text is `{{x}} + {{y}}` and Portuguese text is `{{x}} + {{y}}`
- **THEN** store as `{ "none": "{{x}} + {{y}}" }`

#### Scenario: Different text in each language
- **WHEN** English text is `What is the sum?` and Portuguese text is `Qual é a soma?`
- **THEN** store as `{ "en": "What is the sum?", "pt": "Qual é a soma?" }`

#### Scenario: Per-choice detection
- **WHEN** a question has 4 choices
- **THEN** each choice text is independently evaluated for multilingual vs language-independent storage

---

### Requirement: Database Record Creation

Questions are imported into the existing QuestionTemplate and Choice models.

#### Scenario: QuestionTemplate creation
- **WHEN** importing a question
- **THEN** create a `QuestionTemplate` with:
  - `title`: Derived from filename (e.g., "spa-advantage.yaml" → "Spa Advantage")
  - `text`: Multilingual JSON field
  - `variables`: Converted variable definitions
  - `subject`: The "Uncategorized" root-level Subject

#### Scenario: Uncategorized subject
- **WHEN** the "Uncategorized" subject does not exist
- **THEN** create it as a root-level Subject (no parent)

#### Scenario: Choice creation
- **WHEN** a question has choices defined
- **THEN** create `Choice` objects with:
  - `order=0` for the first choice (correct answer)
  - `order=1, 2, 3...` for subsequent choices
  - `text`: Multilingual JSON field
  - `template`: Link to the parent QuestionTemplate

---

### Requirement: Error Handling and Reporting

The command provides comprehensive feedback about the import process.

#### Scenario: Successful import summary
- **WHEN** import completes
- **THEN** display:
  - Total files processed
  - Questions imported successfully
  - Total choices created
  - Count of language-independent texts
  - Count of language-specific texts

#### Scenario: YAML parsing error
- **WHEN** a YAML file is malformed
- **THEN** skip the file and log: "Failed to parse: filename.yaml - [error details]"
- **THEN** continue processing remaining files

#### Scenario: Database error
- **WHEN** a database operation fails
- **THEN** log the error with question filename
- **THEN** continue processing remaining files

---

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
