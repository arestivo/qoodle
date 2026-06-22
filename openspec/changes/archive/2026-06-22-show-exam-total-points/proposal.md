## Why

The exam detail page shows each question's point value but not the exam total.
Teachers must calculate the sum manually when checking or adjusting an exam.

## Context

Each `QuestionPool` represents one exam question and stores its point value in
`default_grade`. Alternative templates and generated versions do not add extra
questions, so each pool contributes its grade exactly once. No dependency or
schema change is required.

## What Changes

- Sum `default_grade` across all pools belonging to the exam.
- Expose the decimal total in `ExamDetailView`.
- Display the total in the Questions card header.
- Display zero points when the exam has no pools.

## Capabilities

### New Capabilities

- `exam-total-points`: display the total available points on an exam detail page.

### Modified Capabilities

None.

## Impact

The change affects `apps/exams/views.py`,
`apps/exams/templates/exams/exam_detail.html`, and `apps/exams/tests.py`.
There are no model, migration, URL, form, or static-file changes.

Verification will run
`poetry run pytest apps/exams/tests.py -k ExamTotalPoints` and Django system
checks.
