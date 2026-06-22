## MODIFIED Requirements

### Requirement: Form UI for Variable Definition

The question create and edit form MUST provide type-specific fields for each
variable type. For a set variable, items MUST be entered one per line in a
Bootstrap 5.3.8 `textarea.form-control.form-control-sm.var-items`. Each
non-empty trimmed line MUST become one string in the set variable's `items`
array, and commas inside a line MUST remain part of that item.

The form remains available at `GET` and `POST /questions/create/` and
`GET` and `POST /questions/<uuid:pk>/edit/`, for example
`/questions/123e4567-e89b-12d3-a456-426614174000/edit/`.
No model fields change: `QuestionTemplate.variables` remains a JSONField and
set definitions retain `{"type": "set", "items": list[str], "size": int}`.

The existing deferred
`apps/questions/static/questions/js/question_form.js` script MUST remain in the
`extra_js` block inherited from `common/base.html`, where it is already enclosed
by `{% compress js %}`.

#### Scenario: Set item contains a comma

- **GIVEN** a teacher is editing a set variable
- **WHEN** the items textarea contains:

  ```text
  Paris, France
  Porto, Portugal
  London
  ```

- **THEN** the serialized `items` value is
  `["Paris, France", "Porto, Portugal", "London"]`
- **AND** no item is split at a comma

#### Scenario: Blank lines and surrounding whitespace

- **GIVEN** a set items textarea contains blank lines and surrounding whitespace
- **WHEN** the variable definition is serialized
- **THEN** surrounding whitespace is removed from each item
- **AND** blank lines do not create empty items

#### Scenario: Existing set variable is loaded for editing

- **GIVEN** a saved set variable has
  `items = ["Paris, France", "Porto, Portugal"]`
- **WHEN** the question edit form is loaded
- **THEN** the textarea displays `Paris, France` and `Porto, Portugal` on separate lines
- **AND** saving without edits preserves both complete items

#### Scenario: Set generation preserves item punctuation

- **GIVEN** a set variable stores an item `"Paris, France"`
- **WHEN** the variable generator selects that item
- **THEN** the generated value is exactly `"Paris, France"`
