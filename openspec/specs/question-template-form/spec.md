## MODIFIED Requirements

### Requirement: Subject Selector Display

The subject dropdown in the question template form displays full hierarchical paths.

#### Scenario: Subject with parent
- **WHEN** viewing the subject dropdown
- **THEN** a subject "Equations" under "Math > Algebra" displays as "Math > Algebra > Equations"

#### Scenario: Root subject
- **WHEN** viewing the subject dropdown
- **THEN** a root subject "Physics" displays as "Physics"

#### Scenario: Alphabetical sorting by path
- **WHEN** viewing the subject dropdown
- **THEN** subjects are sorted alphabetically by their full path
- **THEN** "Math > Algebra" appears before "Math > Calculus"
- **THEN** "Physics" appears after "Math > Calculus"
