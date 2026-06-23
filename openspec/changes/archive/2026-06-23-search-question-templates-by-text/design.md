## Context

The list view currently builds one queryset and applies subject and state
filters before ordering and pagination.

## Goals / Non-Goals

**Goals:**

- Search title and all language variants of question text.
- Compose with current filters.
- Preserve query state through pagination.

**Non-Goals:**

- Search answer choices, variables, tags, or subjects.
- Add ranking, highlighting, or full-text search infrastructure.
- Add autocomplete or JavaScript requests.

## Decisions

### 1. Filter with a Django Q expression

Trim `q`; when non-empty, apply
`Q(title__icontains=q) | Q(text__icontains=q)`. Existing filters continue to
apply before ordering.

**Alternatives considered:**

- Python-side filtering: rejected because it breaks database pagination.
- Search choices: rejected because the request concerns template/question text
  and would require duplicate handling.
- Database full-text search: rejected as unnecessary for current scale and
  cross-database support.

### 2. Use a normal GET search form

Add the search input and submit button to the existing filter form. Select and
checkbox auto-submission naturally retains the text input. Pagination explicitly
appends an URL-encoded `q`.

### 3. No schema or asset changes

No models, migrations, routes, template tags, CSS, or JavaScript are added.

## Risks / Trade-offs

- JSONField containment is substring search over serialized multilingual
  content, which is sufficient but not ranked.
- Leading and trailing search whitespace is ignored.
