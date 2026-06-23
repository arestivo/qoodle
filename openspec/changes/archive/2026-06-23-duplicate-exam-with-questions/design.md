## Context

Exam-specific configuration is represented by three layers: `Exam`,
`QuestionPool`, and `QuestionPoolTemplate`. Question templates are reusable
content shared across exams.

## Goals / Non-Goals

**Goals:**

- Copy all exam-owned structure and settings.
- Preserve pool ordering, grades, assignments, and version counts.
- Avoid partial duplicates.
- Provide duplication from list and detail pages.

**Non-Goals:**

- Clone question templates or choices.
- Provide a rename dialog before duplication.
- Copy generated Moodle variants.

## Decisions

### 1. Use a POST-only transactional view

Add `ExamDuplicateView(View)` at `<uuid:pk>/duplicate/`. Its `post()` method
loads the source with prefetched pools and memberships, then creates the copy
inside `transaction.atomic()`.

**Alternatives considered:**

- GET endpoint: rejected because duplication changes database state.
- Model `save()` override: rejected because duplication is an explicit workflow,
  not persistence behavior.

### 2. Clone ownership records and reuse content records

Create a new `Exam`, new pools, and new through records. Through records retain
the original `template_id`. This separates exam configuration while preserving
the project's reusable-template architecture.

### 3. Generate a bounded copy title

Append ` (Copy)` after truncating the source title so the result fits the
255-character field. Titles are not unique, so no numeric suffix is necessary.

### 4. Add inline POST forms

Add CSRF-protected POST forms to
`apps/exams/templates/exams/exam_list.html` and
`apps/exams/templates/exams/exam_detail.html`. No frontend assets, template
tags, filters, or migrations are needed.

## Risks / Trade-offs

- Templates remain shared. Editing a template affects every exam that references
  it; this is existing domain behavior.
- Large exams create multiple rows synchronously. Expected exam sizes make a
  transactional request appropriate.
