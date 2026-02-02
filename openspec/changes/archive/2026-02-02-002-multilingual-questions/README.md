# Change: Multilingual Questions

**Status:** Planning  
**Created:** 2026-02-02  
**Schema:** spec-driven

## Summary

Implement a question management system with multilingual support. Questions belong to subjects and consist of question text and multiple choice options. Both question text and choices support multiple languages with intelligent fallback logic.

## Context

Teachers need to create quiz questions that can be displayed in multiple languages. Questions should be organized by subject (building on the hierarchical subjects feature from 001-hierarchical-subjects). The system must support:

- Questions with language-specific and language-independent text
- Multiple choice options per question
- Intelligent language fallback (specific language → language-independent → any available language)
- Viewing questions in all available languages simultaneously

This feature builds upon the hierarchical subjects system and prepares for future parametric/variable substitution functionality.

## Goals

1. Create Question model with multilingual text support
2. Create Choice model for multiple choice options
3. Implement JSON-based language storage for flexible multilingual content
4. Implement convention: first choice (order=0) is always the correct answer
5. Provide CRUD interface for question management
6. Display questions filtered by subject (with option to include sub-subjects)
7. Show question preview in all available languages
8. Implement intelligent language fallback logic

## Non-Goals

- Question types beyond multiple choice (e.g., true/false, short answer, essay)
- Variable substitution and parametric questions (future iteration)
- Correct answer marking (future iteration)
- Question difficulty levels or metadata
- Question import/export
- Question versioning or history
- Auto-translation features

## Scope

### In Scope

- `apps/questions/` - New Django app for question management
  - Models: Question, Choice
  - Views: List (with subject filter), Create, Update, Delete, Preview
  - Forms: QuestionForm with inline choice formsets
  - Templates: Question list, form (with inline choices), preview
  - URLs: RESTful routing
  - Admin: Question and Choice admin
  - Tests: Model tests, view tests, form tests, language fallback tests

### Out of Scope

- Marking correct answers
- Question scoring or point values
- Question randomization
- Question pools or banks
- LMS integration or export
- Question analytics or usage tracking

## Dependencies

- `apps/subjects` - Questions belong to subjects via ForeignKey
- `apps/common.models.UUIDModel` - Questions and choices extend UUIDModel
- Django 6.0.1 JSON field support
- Bootstrap 5.3.8 for UI

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| JSON query performance | Medium | Add GIN index on JSON columns, consider separate translation table if needed |
| Complex language fallback logic | Medium | Implement clear precedence rules, comprehensive testing |
| FormSet complexity for inline choices | Low | Use Django's inlineformset_factory, add client-side add/remove |
| Validation of JSON structure | Medium | Implement custom JSON field validators |

## Success Criteria

- [ ] Question model with multilingual text field (JSON)
- [ ] Choice model with multilingual text field (JSON)
- [ ] Questions can be created with multiple choices inline
- [ ] Questions can be filtered by subject (with toggle for sub-subjects)
- [ ] Preview shows question in all available languages
- [ ] Language fallback works: specific → "none" → any available
- [ ] Can edit questions and their choices
- [ ] Can delete questions (with cascade to choices)
- [ ] All tests pass with >80% coverage
- [ ] Code follows PEP 8 and includes type hints

## Open Questions

- Should we use JSONField or a separate Translation model with ForeignKeys?
  - **Leaning toward:** JSONField for simplicity and flexibility, can migrate later
- Should choices have an order field or use natural ordering?
  - **Suggest:** Add explicit `order` field for control
- How to handle empty language keys in JSON?
  - **Suggest:** Validate that at least one language exists, "none" is valid
- Should we pre-define supported languages or allow any language code?
  - **Suggest:** Allow any language code for flexibility, add language management later
