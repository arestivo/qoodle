## Context

`QuestionTemplate._substitute_variables()` evaluates `{{...}}` placeholders for
both questions and choices. `Choice.get_text()` delegates to that method when a
variable context is supplied. There is no second pass for `$...$`, so those
choice expressions remain literal in previews and Moodle exports.

## Goals / Non-Goals

**Goals:**

- Evaluate complete `$...$` expressions in choice text.
- Reuse the restricted variable evaluator and current generated values.
- Support embedded and multiple expressions.
- Preserve invalid and unmatched expressions literally.

**Non-Goals:**

- Apply dollar evaluation to question text.
- Change `{{...}}` behavior.
- Add LaTeX or currency escaping rules.
- Change storage, forms, templates, or frontend assets.

## Decisions

### 1. Add a focused choice-expression helper to QuestionTemplate

`QuestionTemplate._evaluate_dollar_expressions(text, variables)` will replace
non-empty, single-line segments matching `$...$`. Each expression is evaluated
with `VariableGenerator.evaluate_expression()`. Values use the existing display
format: lists are joined with `", "`, and other results use `str()`.

The helper belongs on `QuestionTemplate` because that class owns variable
evaluation and `Choice` already delegates substitution to its template.

**Alternatives considered:**

- Evaluate directly in `Choice`: rejected because it duplicates variable
  evaluator and formatting logic.
- Extend `_substitute_variables()` globally: rejected because question text
  must not gain dollar semantics.
- Use unrestricted Python `eval`: rejected as unsafe.

### 2. Process braces before dollars in Choice.get_text

When `variables is not None`, `Choice.get_text()` will:

1. apply `_substitute_variables()`;
2. apply `_evaluate_dollar_expressions()`.

Testing against `None`, rather than truthiness, allows constant expressions such
as `$2 + 2$` to be evaluated during variant generation even when the template
has no generated variables. Calls that omit a variable context, such as admin
labels, retain literal source text.

### 3. Fail soft for invalid expressions

If restricted evaluation raises `ValidationError`, the complete `$...$`
segment remains unchanged. Unmatched dollar signs do not match the pattern and
also remain unchanged. This mirrors existing `{{...}}` failure behavior and
prevents one malformed choice from crashing preview or export.

### 4. No Django surface changes

There are no database schema, model field, relationship, migration, URL,
template inheritance, template tag, filter, CSS, or JavaScript changes.
Existing preview and export paths consume `Choice.get_text()` and therefore
receive the behavior automatically.

## Risks / Trade-offs

- Paired dollar signs conventionally used for math or currency now opt into
  evaluation in choices. This is the requested delimiter contract.
- The simple delimiter grammar does not support a literal dollar sign inside an
  expression. That can be added later with an explicit escaping specification.
- Fail-soft handling can leave invalid expressions in output. This is
  consistent with current placeholders and preserves backward compatibility.
