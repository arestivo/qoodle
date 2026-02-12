## Why

Templates currently have no lifecycle state — once created, they appear identically everywhere regardless of whether they've been fully reviewed. This makes it hard to track which templates are ready for use in exams and which still need work. Adding a state field (Draft, Completed, Reviewed) provides a clear workflow for template quality control and prevents unreviewed templates from being accidentally added to exams.

## Context

This builds on the existing QuestionTemplate model in `apps/questions/models.py`, which already has fields for title, subject, tags, text, variables, and validation_rules. The template listing page (`question_list.html`) already supports filtering by subject and bulk actions (move, delete). The exam pool template add view (`PoolTemplateAddView`) fetches available templates for selection. No new dependencies are needed.

## What Changes

- Add a `state` CharField to QuestionTemplate with choices: `draft`, `completed`, `reviewed` (default: `draft`)
- Show a green checkmark icon next to reviewed templates in the template list
- Add a state filter dropdown to the template list page
- Restrict the exam pool template add view to only show templates with state `reviewed`
- Show the state on the template preview page and in the edit form
- Show state in exam detail and pool template add views

## Capabilities

### New Capabilities

- **state-field**: CharField with choices on QuestionTemplate model, with default `draft`
- **state-display**: Visual indicator (green checkmark) for reviewed templates across all listing views
- **state-filter**: Filter dropdown on the template list page to filter by state

### Modified Capabilities

- **exam-template-selection**: Pool template add view restricted to only show `reviewed` templates

## Impact

- Existing templates will default to `draft` state after migration — users will need to update templates to `reviewed` before they appear in exam template selection
- The template list page will gain a new filter control for state
- No breaking changes to the data model (additive field with default)

## Verification Plan

- Run `poetry run python manage.py test apps.questions` to verify model and view tests pass
- Verify that only reviewed templates appear in the pool template add view
- Verify the state filter works on the template list page

## Risks

- Existing templates defaulting to `draft` means they won't be selectable for exams until manually updated — users should be aware of this when migrating
