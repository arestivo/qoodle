## Why

Moodle XML tags currently use the global exported variant number. If question
pool 1 produces multiple versions, those versions receive `q1`, `q2`, and so
on, which incorrectly identifies them as different source questions. Moodle
tags should group every generated variant by its source question pool.

## Context

This builds on the existing Moodle XML export in `apps/exams/moodle_export.py`.
Question pools define the exam question position through their `order` field,
while pool templates and their versions produce alternative questions for that
position. The export already has access to the pool order while generating each
variant. No dependency change is needed; `pyproject.toml` already contains all
runtime requirements.

## What Changes

- Generate each Moodle tag from the containing question pool order.
- Preserve sequential exported question names.
- Add regression coverage proving that all versions and templates in one pool
  share a tag and a later pool uses its own tag.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `moodle-xml-export`: exported variants are grouped by source question pool
  using the tag `q{pool.order}`.

## Impact

Only Moodle XML tag values and related tests change. There are no Django model,
migration, URL, view, template, or dependency changes. The main risk is
confusing global export sequence with pool identity; tests will parse the XML
and assert both the complete tag sequence and unchanged question names.

Verification will run
`poetry run pytest apps/exams/tests.py -k MoodleXMLGenerationTests`.
This change does not alter Django ORM behavior; it reads the existing
`QuestionPool.order` field using the documented model attribute interface.
