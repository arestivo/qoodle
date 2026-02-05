# Tasks: Subject Selector Path

## Implementation

- [x] Update `QuestionTemplateForm.__init__` to customize subject field:
  - Sort subjects by full path
  - Set `label_from_instance` to use `get_full_path()`

## Testing

- [x] Verify dropdown shows full paths
- [x] Verify sorting is alphabetical by path
