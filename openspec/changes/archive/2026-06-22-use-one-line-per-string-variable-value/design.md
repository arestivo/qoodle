## Context

The string editor loads arrays with `join(', ')` and saves them with
`split(',')`. This makes commas ambiguous. The stored JSON array is already
unambiguous.

## Goals / Non-Goals

**Goals:**

- Preserve commas inside string-variable options.
- Use the same interaction pattern as set items.
- Preserve existing stored values without migration.

**Non-Goals:**

- Change string generation or validation.
- Change set-variable behavior.
- Introduce CSV quoting or escaping.

## Decisions

### 1. Use a multiline textarea

Replace `.var-values` with a four-row textarea in
`apps/questions/templates/questions/question_form.html`. Update help text to
state one value per line and show a comma-containing example.

**Alternatives considered:**

- CSV quoting and escaped commas: rejected as less discoverable.
- Dynamic option rows: rejected as unnecessary UI complexity.

### 2. Use newline serialization

`question_form.js` will load with `config.values.join('\n')` and save with
`split(/\r?\n/)`, trimming entries and filtering blank lines.

### 3. No Django schema or routing changes

`QuestionTemplate.variables` remains a JSONField. No migrations, model fields,
relationships, forms, views, URLs, template tags, filters, CSS, or additional
static files are required.

## Risks / Trade-offs

- Existing users must use line breaks instead of commas between options.
- Leading/trailing whitespace is normalized; internal whitespace and
  punctuation are preserved.
