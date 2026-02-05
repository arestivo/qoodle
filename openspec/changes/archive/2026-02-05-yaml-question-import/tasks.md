# Tasks: YAML Question Import Script

## Phase 1: Setup and Basic Structure

- [x] Create `import_yaml_questions.py` management command in `apps/questions/management/commands/`
- [x] Add argparse for folder path argument
- [x] Add basic error handling and logging
- [x] Add check to verify folder exists and has `en/` and `pt/` subdirectories

## Phase 2: YAML Parsing

- [x] Implement YAML file discovery (find all `.yaml` or `.yml` files in both language folders)
- [x] Validate that each English file has a corresponding Portuguese file (same filename)
- [x] Implement YAML parsing with proper error handling for malformed files
- [x] Parse question type, variables, text, and choices from YAML structure

## Phase 3: Variable Conversion

- [x] Convert variable syntax from YAML to model format:
  - `values` → `items` for set type variables
  - Handle `num`, `string`, `set`, and `expression` types
- [x] Convert variable references in text from `<var>` to `{{var}}` syntax
- [x] Handle array indexing: `<c[0]>` → `{{c[0]}}`
- [x] Validate converted variable definitions match model requirements

## Phase 4: Multilingual Text Handling

- [x] Compare English and Portuguese text for each question
- [x] If text is identical in both languages, create language-independent entry with key "none"
- [x] If text differs, create separate entries with keys "en" and "pt"
- [x] Apply same logic for each choice text
- [x] Log multilingual decisions for review

## Phase 5: Database Operations

- [x] Get or create "Uncategorized" root-level Subject
- [x] Create QuestionTemplate with:
  - Title derived from filename (e.g., "spa-advantage" → "Spa Advantage")
  - Multilingual text field
  - Converted variables
  - Subject = "Uncategorized"
- [x] Create Choice objects for each choice:
  - Multilingual text field
  - order = 0 for first choice (correct answer), 1+ for others
  - Link to QuestionTemplate

## Phase 6: Error Handling and Reporting

- [x] Add try/except blocks for file operations
- [x] Add try/except blocks for YAML parsing errors
- [x] Add try/except blocks for database operations
- [x] Track and report:
  - Number of files processed
  - Number of questions imported successfully
  - Number of choices created
  - Number of language-independent vs language-specific texts
  - List of failed imports with error messages

## Phase 7: Testing and Validation

- [x] Run script on sample folder with 2-3 test questions
- [x] Verify QuestionTemplate objects created correctly in database
- [x] Verify Choice objects linked properly with correct order
- [x] Verify multilingual text stored correctly (none/en/pt keys)
- [x] Verify variables converted correctly
- [x] Test preview rendering of imported questions

## Notes

**YAML Variable Syntax Conversion:**
```yaml
# YAML format (input)
vars:
  c: { type: set, values: ['A', 'B', 'C'], size: 1 }

# Model format (output)
variables = {
    "c": {"type": "set", "items": ["A", "B", "C"], "size": 1}
}
```

**Text Reference Conversion:**
```
# YAML format (input)
text: "Choose <c[0]>"

# Model format (output)
text: {"none": "Choose {{c[0]}}"}  # if same in both languages
# or
text: {"en": "Choose {{c[0]}}", "pt": "Escolha {{c[0]}}"}  # if different
```

**Multilingual Logic:**
- Compare `en/<file>.yaml` text with `pt/<file>.yaml` text
- If identical → use `{"none": "text"}`
- If different → use `{"en": "en_text", "pt": "pt_text"}`
- Apply to question text AND each choice text independently
