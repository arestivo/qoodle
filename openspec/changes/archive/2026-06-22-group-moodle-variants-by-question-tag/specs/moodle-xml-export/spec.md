## MODIFIED Requirements

### Requirement: Moodle XML Generation

The system MUST tag every exported question variant with the identifier of its
source `QuestionPool`. `QuestionPool.order` is a positive integer and the
Moodle tag MUST be formatted as `q{order}`. Exported question names MAY remain
globally sequential and unique.

The existing export URL remains
`/exams/<uuid:pk>/export/`, for example
`/exams/123e4567-e89b-12d3-a456-426614174000/export/`.
This change has no Bootstrap components, templates, static files, CSS, or
JavaScript and therefore requires no `{% compress %}` blocks.

#### Scenario: Multiple versions of question one share q1

- **GIVEN** question pool 1 contains one template configured for three versions
- **WHEN** the Moodle XML export is generated
- **THEN** all three exported questions contain the tag `q1`
- **AND** none of those variants is tagged `q2` or `q3`

#### Scenario: Multiple templates in one pool share the pool tag

- **GIVEN** question pool 1 contains multiple templates and versions
- **WHEN** the Moodle XML export is generated
- **THEN** every exported question produced by that pool contains the tag `q1`

#### Scenario: Later question pool uses its own tag

- **GIVEN** question pool 1 and question pool 2 both produce variants
- **WHEN** the Moodle XML export is generated
- **THEN** variants from pool 1 contain the tag `q1`
- **AND** variants from pool 2 contain the tag `q2`
