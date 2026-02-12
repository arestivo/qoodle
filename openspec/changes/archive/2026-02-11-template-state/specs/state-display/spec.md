## ADDED Requirements

### Requirement: Visual state indicator on template listings

Reviewed templates show a green checkmark icon across all views where templates are listed. The checkmark uses FontAwesome `fa-solid fa-circle-check` with `text-success` class.

#### Scenario: Reviewed template in template list
- **GIVEN** a template with state `reviewed`
- **WHEN** the template list page (`question_list.html`) is rendered
- **THEN** a green checkmark `<i class="fa-solid fa-circle-check text-success">` appears next to the template title

#### Scenario: Draft template in template list
- **GIVEN** a template with state `draft`
- **WHEN** the template list page is rendered
- **THEN** no checkmark icon appears next to the template title

#### Scenario: Completed template in template list
- **GIVEN** a template with state `completed`
- **WHEN** the template list page is rendered
- **THEN** no checkmark icon appears (only `reviewed` gets the checkmark)

#### Scenario: State shown in exam detail template list
- **GIVEN** a pool template whose template has state `reviewed`
- **WHEN** the exam detail page (`exam_detail.html`) is rendered
- **THEN** a green checkmark appears inline with the template title, subject, tags, and versions badge

#### Scenario: State shown in pool template add list
- **GIVEN** a template with state `reviewed` in the available templates
- **WHEN** the pool template add page (`pool_template_add.html`) is rendered
- **THEN** a green checkmark appears inline with the template title and other badges

### Display Rules

- Only `reviewed` state shows the green checkmark
- The checkmark appears immediately before or after the template title
- Use `<i class="fa-solid fa-circle-check text-success" title="Reviewed"></i>` with a tooltip
