## ADDED Requirements

### Requirement: Tags field on QuestionTemplate

A new `tags` field on the `QuestionTemplate` model stores comma-separated tag strings. The field is a `CharField(max_length=500, blank=True, default="")`.

#### Scenario: Template created without tags
- **GIVEN** a QuestionTemplate with no tags provided
- **WHEN** the template is saved
- **THEN** the `tags` field is stored as an empty string `""`

#### Scenario: Template created with tags
- **GIVEN** a QuestionTemplate with `tags` set to `"easy, exam-2024, review"`
- **WHEN** the template is saved
- **THEN** the `tags` field stores `"easy, exam-2024, review"`

#### Scenario: Tags are stripped and normalized
- **GIVEN** a QuestionTemplate with `tags` set to `" easy ,  exam-2024 , review "`
- **WHEN** `tag_list()` is called
- **THEN** the result is `["easy", "exam-2024", "review"]` (whitespace stripped, empty strings removed)

### Requirement: tag_list helper method

A `tag_list()` method on `QuestionTemplate` returns the tags as a Python list of stripped strings, filtering out empty entries.

#### Scenario: Empty tags field
- **GIVEN** a template with `tags = ""`
- **WHEN** `tag_list()` is called
- **THEN** the result is `[]`

#### Scenario: Tags with whitespace
- **GIVEN** a template with `tags = "easy, , hard"`
- **WHEN** `tag_list()` is called
- **THEN** the result is `["easy", "hard"]`
