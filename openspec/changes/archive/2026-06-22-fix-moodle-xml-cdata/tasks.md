## Implementation Tasks

- [x] In `apps/exams`, update `moodle_export.py` so question and answer HTML is
  converted to real `minidom` CDATA nodes during serialization.
- [x] In `apps/exams`, update `tests.py` to assert genuine question and answer
  CDATA syntax, absence of escaped CDATA markers, parsed HTML content, and safe
  handling of embedded CDATA terminators.
- [x] Verify the focused behavior with
  `poetry run pytest apps/exams/tests.py -k "MarkdownConversion or MoodleXMLGeneration"`.
- [x] Verify the modified app and coverage with
  `poetry run pytest apps/exams/tests.py -o addopts='' --cov=apps.exams --cov-fail-under=80`.
- [x] Run `poetry run openspec validate fix-moodle-xml-cdata`, mark completed
  tasks, and archive the validated change.
