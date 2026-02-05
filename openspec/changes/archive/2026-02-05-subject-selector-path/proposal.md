## Why

When editing a question template, the subject dropdown shows only the subject name without its hierarchical path. This makes it hard to distinguish between subjects with the same name in different parts of the hierarchy. The question list filter already shows full paths and sorts hierarchically - the form should match this behavior.

## What Changes

Update the `QuestionTemplateForm` to:
1. Display subjects with their full path (e.g., "Math > Algebra > Equations")
2. Sort subjects alphabetically by full path

## Capabilities

### New Capabilities

_None - this modifies existing functionality_

### Modified Capabilities

- **question-template-form**: Subject selector shows full path and sorts hierarchically

## Impact

- **Low risk**: Only affects the display of the subject dropdown in the form
- **No database changes**: Uses existing `Subject.get_full_path()` method
- **Consistent UX**: Matches the pattern already used in the question list filter
