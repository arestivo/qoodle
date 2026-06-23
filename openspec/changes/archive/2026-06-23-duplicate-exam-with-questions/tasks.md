## Implementation Tasks

- [x] In `apps/exams/views.py`, implement atomic exam duplication that copies
  pools and memberships while reusing templates.
- [x] In `apps/exams/urls.py`, add the POST duplication route.
- [x] In `apps/exams/templates/exams/exam_list.html`, add a CSRF-protected
  duplicate action.
- [x] In `apps/exams/templates/exams/exam_detail.html`, add a CSRF-protected
  duplicate action.
- [x] In `apps/exams/tests.py`, add `ExamDuplicationTests` for metadata,
  structure, template reuse, empty exams, title length, POST behavior, redirect,
  messages, and UI controls.
- [x] Run focused and full exams-app tests, coverage, Ruff, Django checks, and
  strict OpenSpec validation.
- [x] Archive the completed change.
