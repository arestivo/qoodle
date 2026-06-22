## Context

The set-variable editor uses a single-line text input. `question_form.js`
serializes it with `split(',')` and loads saved arrays with `join(', ')`.
Consequently, the UI cannot distinguish a separator comma from a comma that is
part of an item. The persisted model format is already unambiguous because
`QuestionTemplate.variables` stores `items` as a JSON array.

## Goals / Non-Goals

**Goals:**

- Preserve commas inside set items.
- Make item boundaries explicit and easy to edit.
- Preserve existing stored arrays without migration.
- Ignore blank lines and trim surrounding whitespace.

**Non-Goals:**

- Change string-variable value input.
- Introduce CSV quoting or escaping syntax.
- Change set generation or substitution semantics.

## Decisions

### 1. Use one set item per textarea line

`apps/questions/templates/questions/question_form.html`, which extends
`common/base.html`, will replace `.var-items` from an `<input type="text">` to
a `<textarea rows="4">`. Help text will explicitly say “one item per line” and
show a comma-containing example.

This matches the existing variable-system specification and makes commas
ordinary item content.

**Alternatives considered:**

- CSV quoting: rejected because it adds escaping rules and makes ordinary
  authoring harder.
- Backslash-escaped commas: rejected because it is less discoverable and
  requires additional escape handling.
- A dynamic add/remove item widget: rejected as unnecessary complexity for
  multiline strings.

### 2. Serialize and load with newline boundaries

In `apps/questions/static/questions/js/question_form.js`:

- Load `config.items` with `join('\n')`.
- Serialize with `split(/\r?\n/)`, trim each line, and remove empty lines.

Windows and Unix line endings are both accepted. Internal punctuation,
including commas, remains unchanged.

### 3. No backend or schema changes

There are no database, model, field, relationship, migration, form-class, view,
or URL changes. Existing routes remain `/questions/create/` and
`/questions/<uuid:pk>/edit/`. No template tags, filters, or CSS files are
needed. The JavaScript remains under `apps/questions/static/questions/js/` and
is delivered through the inherited compressed `extra_js` block.

## Risks / Trade-offs

- Users must enter separate items on separate lines instead of commas. Updated
  placeholder, title, and help text make this explicit.
- Leading and trailing whitespace cannot be preserved because item values are
  normalized with `trim()`. Internal whitespace and punctuation are preserved.
- Browser-level JavaScript tests are not currently configured. Regression tests
  will verify the form markup, serialization contract in the static script,
  stored JSON behavior, and generator preservation.
