## Context

The import command in `apps/questions/management/commands/import_yaml_questions.py` needs enhanced error handling and conditions support.

## Goals / Non-Goals

**Goals:**
- Validate templates can render after import
- Skip duplicate templates
- Convert YAML conditions to validation_rules

**Non-Goals:**
- Change the validation_rules execution logic (already works)
- Support other duplicate detection strategies

## Decisions

### 1. Validate by Rendering with Seed

After creating a template, call `template.generate_variables(seed=0)` and `template.get_text(variables=vars)`. Using a fixed seed ensures reproducible validation.

**Alternatives considered:**
- Just call `template.clean()`: Doesn't catch all runtime errors

### 2. Delete Failed Templates in Same Transaction

Wrap create + validate in a transaction. If validation fails, the transaction rolls back automatically.

**Alternatives considered:**
- Explicit delete after failed validation: More complex, same result

### 3. Convert Variable References with Regex

Use regex `<(\w+)>` to match variable references like `<r>` but not comparison operators like `<` or `>` alone.

Pattern: `<(\w+(?:\[\d+\])?)>` → captures `<var>` and `<var[0]>` but not `< 10` or `> 5`.

**Alternatives considered:**
- Simple replace: Would break `<` and `>` comparison operators

## Risks / Trade-offs

- **Performance**: Rendering each template adds overhead. Acceptable for import operations.
- **False negatives**: A template might fail with certain seeds but pass with seed=0. Acceptable tradeoff.
