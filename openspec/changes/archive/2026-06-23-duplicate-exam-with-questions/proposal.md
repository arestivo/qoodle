## Why

Teachers often need a new exam based on an existing structure. Recreating every
question pool, grade, template assignment, and version count manually is slow
and error-prone.

## Context

An `Exam` owns ordered `QuestionPool` records, and each pool links reusable
`QuestionTemplate` records through `QuestionPoolTemplate`. Duplication should
copy the exam-specific structure while retaining references to the shared
question templates. No dependency or schema change is required.

## What Changes

- Add a POST-only duplicate-exam endpoint.
- Copy exam metadata with a ` (Copy)` title suffix.
- Copy every pool with its order and default grade.
- Copy every pool-template assignment and number of versions.
- Reuse existing question-template records.
- Add Duplicate actions to exam list and detail pages.
- Redirect to the new exam and show a success message.

## Capabilities

### New Capabilities

- `exam-duplication`: duplicate an exam and its complete question structure.

### Modified Capabilities

None.

## Impact

The change affects exam routes, views, list/detail templates, and tests. It does
not add models or migrations. Duplication will run in a database transaction so
partial copies are rolled back if any operation fails.

Verification will run
`poetry run pytest apps/exams/tests.py -k ExamDuplication` and the complete
exams-app test suite.
