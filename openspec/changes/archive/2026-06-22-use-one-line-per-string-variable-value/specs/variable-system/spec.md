## MODIFIED Requirements

### Requirement: Form UI for Variable Definition

The variable-definition form MUST use one-value-per-line textareas for both
string-variable `values` and set-variable `items`. Commas inside a line MUST be
preserved as content. The existing deferred question-form JavaScript remains in
the inherited `extra_js` block covered by `{% compress js %}` in
`common/base.html`.

#### Scenario: String type fields

- **GIVEN** the teacher selects variable type `string`
- **WHEN** type-specific fields are displayed
- **THEN** a multiline textarea appears for entering one possible value per line
- **AND** help text explains that commas inside a line are preserved

#### Scenario: Set type fields remain unchanged

- **GIVEN** the teacher selects variable type `set`
- **WHEN** type-specific fields are displayed
- **THEN** the existing one-item-per-line textarea and subset-size input remain available
