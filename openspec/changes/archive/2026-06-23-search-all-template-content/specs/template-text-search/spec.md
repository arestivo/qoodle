## MODIFIED Requirements

### Requirement: Search templates by title or question text

The template list at `GET /questions/` MUST accept a `q` query parameter and
return templates whose title, multilingual question-text JSON, or multilingual
answer-choice text contains the trimmed term case-insensitively. Each matching
template MUST appear only once.

#### Scenario: Search by answer choice

- **GIVEN** a search term exists only in an answer choice
- **WHEN** the template list is searched
- **THEN** the template containing that choice is included

#### Scenario: Search multilingual answer-choice text

- **GIVEN** a choice contains the Portuguese text `Lisboa`
- **WHEN** `/questions/?q=lisboa` is requested
- **THEN** its template is included regardless of which language is displayed

#### Scenario: Multiple matching choices do not duplicate a template

- **GIVEN** two choices belonging to one template contain the search term
- **WHEN** the template list is searched
- **THEN** that template is returned once

#### Scenario: Blank search does not filter

- **WHEN** `q` is missing, empty, or whitespace-only
- **THEN** templates are not filtered by text
