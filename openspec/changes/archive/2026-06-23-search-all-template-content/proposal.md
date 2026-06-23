## Why

Template authors often remember wording from an answer choice rather than the
question title or prompt. Restricting search to titles and question text makes
those templates unnecessarily difficult to find.

## What Changes

- Extend template-list text search to all visible problem text: title,
  multilingual question text, and multilingual answer-choice text.
- Keep search case-insensitive and compatible with the existing filters and
  pagination.
- Ensure a template appears only once when multiple choices match.

## Capabilities

### Modified Capabilities

- `template-text-search`: answer-choice text becomes searchable.

## Impact

The change affects the questions list queryset, search tests, and the
`template-text-search` specification. It requires no model or migration change.
