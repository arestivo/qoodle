## Why

The exam detail page renders a subject link for each template in a question
pool, but the template variable in the `href` is malformed. The link should use
the subject UUID and follow the existing convention of opening the question
template list filtered to that subject.

## What Changes

- Fix the malformed subject-link template expression on the exam detail page.
- Add regression coverage for the rendered subject link.

## Impact

Affected files:

- `apps/exams/templates/exams/exam_detail.html`
- `apps/exams/tests.py`
