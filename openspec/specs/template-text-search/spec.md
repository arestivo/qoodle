# template-text-search Specification

## Purpose
TBD - created by archiving change search-question-templates-by-text. Update Purpose after archive.
## Requirements
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

### Requirement: Search composes with template filters

Text search MUST combine with the existing subject, include-sub-subjects, and
state filters using logical AND.

#### Scenario: Combined search and state filter

- **GIVEN** matching templates exist in draft and reviewed states
- **WHEN** `q` is supplied with `state=reviewed`
- **THEN** only reviewed matching templates are returned

#### Scenario: Search term persists through pagination

- **GIVEN** search results span multiple pages
- **WHEN** pagination links are rendered
- **THEN** each previous or next URL preserves the encoded `q` parameter

### Requirement: Template search form

The filter card MUST contain a Bootstrap 5.3.8 search input with `name="q"`,
`id="search"`, and a submit button using the FontAwesome `fa-magnifying-glass`
icon. The current search term MUST remain visible after submission. The
existing Clear Filter action MUST clear search and all filters. No JavaScript or
CSS change is required.

#### Scenario: Search form preserves current term

- **WHEN** the list is rendered for `?q=network`
- **THEN** the search input value is `network`
