## Implementation Tasks

- [x] In `apps/exams/moodle_export.py`, derive Moodle tag text from
  `QuestionPool.order` while preserving sequential exported question names.
- [x] In `apps/exams/tests.py`, add parsed XML regression coverage for multiple
  versions and templates sharing one pool tag and for a later pool using its
  own tag.
- [x] Verify focused behavior with
  `poetry run pytest apps/exams/tests.py -k MoodleXMLGenerationTests`.
- [x] Verify the app test suite and coverage with
  `poetry run pytest apps/exams/tests.py -o addopts='' --cov=apps.exams --cov-fail-under=80`.
- [x] Run
  `poetry run openspec validate group-moodle-variants-by-question-tag`, mark
  tasks complete, and archive the change.
