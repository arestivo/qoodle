## Why

As the template library grows, subject and state filters are insufficient for
finding a template whose title or question wording is known.

## Context

`QuestionListView` already composes subject and state filters over
`QuestionTemplate`. Titles are stored in a CharField and multilingual question
content is stored in the `text` JSONField. Django can apply case-insensitive
containment to both without a schema change or new dependency.

## What Changes

- Add a search field to the template-list filter card.
- Search case-insensitively across title and all multilingual question text.
- Combine search with subject, descendant, and state filters.
- Preserve the search term through pagination and filter submissions.
- Exclude answer-choice text from matching.

## Capabilities

### New Capabilities

- `template-text-search`: search the question-template library by title or question text.

### Modified Capabilities

None.

## Impact

The change affects the questions list view, template, and tests. There are no
model, migration, URL, or static-file changes.

Verification will run
`poetry run pytest apps/questions/tests.py -k TemplateTextSearch` and Django
system checks.
