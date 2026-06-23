## Context

`QuestionListView` currently searches `QuestionTemplate.title` and
`QuestionTemplate.text`. Choices are related through the `choices` reverse
foreign key and store multilingual content in their own `text` JSONField.

## Decision

Add `choices__text__icontains` to the existing OR search predicate and call
`distinct()` on the filtered queryset. This keeps the existing single-term
search behavior while preventing duplicate templates when more than one choice
contains the term.

Search covers visible problem wording only. Internal variable definitions and
validation rules remain configuration rather than user-facing problem text.

## Verification

Tests will cover matching choice text case-insensitively and returning one
template when multiple choices match.
