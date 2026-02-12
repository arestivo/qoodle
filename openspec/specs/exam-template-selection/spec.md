## MODIFIED Requirements

### Requirement: Only reviewed templates selectable for exams

The pool template add view (`PoolTemplateAddView`) must only show templates with state `reviewed` in the available templates list. Non-reviewed templates are excluded from selection.

#### Scenario: Only reviewed templates shown
- **GIVEN** templates exist with states `draft`, `completed`, and `reviewed`
- **WHEN** the pool template add page is loaded
- **THEN** only templates with state `reviewed` appear in the available templates list

#### Scenario: Draft template not shown
- **GIVEN** a template with state `draft`
- **WHEN** the pool template add page is loaded
- **THEN** the draft template does not appear in the available templates list

#### Scenario: No reviewed templates available
- **GIVEN** all templates have state `draft` or `completed`
- **WHEN** the pool template add page is loaded
- **THEN** the "no available templates" alert is shown

#### Scenario: Existing pool templates with non-reviewed state
- **GIVEN** a pool template was added when it was `reviewed`, but later its template state was changed to `draft`
- **WHEN** the exam detail page is loaded
- **THEN** the pool template is still shown (no retroactive removal)

### Implementation

- In `PoolTemplateAddView.get_context_data()`, add `.filter(state="reviewed")` to the `available_templates` queryset
- This filter is applied in addition to the existing exclusion of templates already used in the exam
