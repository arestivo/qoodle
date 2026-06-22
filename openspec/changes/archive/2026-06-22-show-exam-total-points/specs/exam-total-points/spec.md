## ADDED Requirements

### Requirement: Exam total points display

The exam detail page MUST display the sum of `QuestionPool.default_grade` for
all pools belonging to the exam. Every pool MUST contribute exactly once,
regardless of its number of templates or generated versions.

The total MUST be shown in the Questions card header at
`GET /exams/<uuid:pk>/`, for example
`/exams/123e4567-e89b-12d3-a456-426614174000/`, using a Bootstrap 5.3.8
`badge bg-primary` with a FontAwesome `fa-star` icon. No CSS, JavaScript, or
`{% compress %}` changes are required.

#### Scenario: Exam with multiple question grades

- **GIVEN** an exam has pools worth `1.00`, `2.50`, and `0.50` points
- **WHEN** the exam detail page is viewed
- **THEN** it displays `Total: 4.00 points`

#### Scenario: Templates and versions do not multiply points

- **GIVEN** one pool is worth `2.50` points
- **AND** the pool contains multiple templates and versions
- **WHEN** the exam detail page is viewed
- **THEN** that pool contributes `2.50` points to the total exactly once

#### Scenario: Empty exam

- **GIVEN** an exam has no question pools
- **WHEN** the exam detail page is viewed
- **THEN** it displays `Total: 0.00 points`

#### Scenario: Total updates after grade change

- **GIVEN** an exam total is displayed
- **WHEN** a pool's default grade is updated and the detail page reloads
- **THEN** the displayed total reflects the updated grade
