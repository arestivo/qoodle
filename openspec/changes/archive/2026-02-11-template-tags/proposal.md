## Why

Templates are currently organized only by subject hierarchy. While subjects provide structural categorization, they don't support cross-cutting labels — for example, marking templates as "easy", "exam-2024", or "review" regardless of which subject they belong to. Tags provide a lightweight, flexible way to annotate and visually identify templates across different views.

## Context

This builds on the existing QuestionTemplate model in the `questions` app. Templates already have a `subject` foreign key for hierarchical organization and are displayed in two listing views: the main question list (`questions:list`) and the pool template add view (`exams:pool_template_add`). Tags complement the subject system without replacing it.

## What Changes

- Add a `tags` field to the `QuestionTemplate` model as a comma-separated `CharField`
- Display tags as Bootstrap badges in the template listing table and in the pool template add view
- Allow editing tags through the existing template create/edit form

## Capabilities

### New Capabilities
- **tag-storage**: Store comma-separated tags on each template via a new `tags` CharField
- **tag-display**: Show tags as badges in the question list and pool template add views
- **tag-editing**: Edit tags through the existing question form (simple text input, comma-separated)

### Modified Capabilities
- **question-list**: Add a tags column/badges to the template listing table
- **pool-template-add**: Show tag badges alongside each template in the add-to-pool view
- **question-form**: Add a tags input field to the create/edit form

## Impact

- Requires a database migration to add the `tags` field (nullable/blank CharField, no data loss)
- No changes to existing subject-based organization — tags are additive
- No new dependencies needed (simple CharField, Bootstrap badge rendering)

## Risks

- Comma-separated storage limits future querying (no efficient tag-based filtering). Acceptable for the current scope (display only), but could be revisited if tag filtering is needed later.

## Verification Plan

- Unit test: create a template with tags, verify they are stored and retrieved correctly
- Template rendering test: verify badges appear in the question list and pool template add views
