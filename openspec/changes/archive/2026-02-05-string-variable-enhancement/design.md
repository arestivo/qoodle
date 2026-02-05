## Context

The `VariableGenerator` class in `apps/questions/models.py` handles variable generation for question templates. The string type currently generates random characters, but needs to select from a predefined list instead.

## Goals / Non-Goals

**Goals:**
- Change string variable to select from a `values` list
- Update validation to require `values` field
- Maintain consistent behavior with set variables (random selection)

**Non-Goals:**
- Support both old and new format (breaking change is acceptable)
- Add weighted selection or other advanced features

## Decisions

### 1. Reuse random.choice for Selection

Use `random.choice(values)` to select a single item, matching how Python's random module works.

**Alternatives considered:**
- Using `random.sample(values, 1)[0]`: More verbose, no benefit over `random.choice`

### 2. Remove Old Parameters

Remove `min_length` and `max_length` validation entirely rather than making them optional.

**Alternatives considered:**
- Supporting both formats: Rejected to keep the codebase simple and consistent

### 3. Align with Set Variable Structure

Use `values` as the key name (same as set variables use for their items in YAML import).

**Alternatives considered:**
- Using `items` like the internal set format: Rejected because `values` is more intuitive for a simple list

## Risks / Trade-offs

- **Breaking change**: Any existing string variables will fail validation. This is acceptable as the old format produced unusable output.
- **No migration path**: Users must manually update any existing string variable definitions.
