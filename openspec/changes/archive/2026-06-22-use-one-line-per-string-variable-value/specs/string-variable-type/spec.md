## MODIFIED Requirements

### Requirement: String Variable Definition

String variables MUST select a random value from a predefined `values` list.
In the question create and edit UI, values MUST be entered one per line in a
Bootstrap 5.3.8 `textarea.form-control.form-control-sm.var-values`. Each
non-empty trimmed line MUST become one array entry, and commas inside a line
MUST remain part of that value.

#### Scenario: Value contains a comma

- **GIVEN** the values textarea contains:

  ```text
  Paris, France
  Porto, Portugal
  London
  ```

- **WHEN** the variable is serialized
- **THEN** `values` is `["Paris, France", "Porto, Portugal", "London"]`

#### Scenario: Existing values load one per line

- **GIVEN** a saved variable has `values=["Paris, France", "London"]`
- **WHEN** its question is edited
- **THEN** each complete value appears on its own textarea line
- **AND** saving without changes preserves both values

#### Scenario: Blank lines are ignored

- **GIVEN** the textarea contains blank lines and surrounding whitespace
- **WHEN** values are serialized
- **THEN** blank lines are removed
- **AND** surrounding whitespace is trimmed

#### Scenario: Existing stored string variables remain compatible

- **GIVEN** an existing variable stores a JSON list of string values
- **WHEN** values are generated
- **THEN** generation continues selecting complete entries from that list
