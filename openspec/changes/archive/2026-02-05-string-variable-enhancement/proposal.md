## Why

The current string variable type generates random strings with configurable length (`min_length`, `max_length`), producing gibberish like "xkqwp". This is rarely useful for quiz questions where meaningful words or phrases are needed.

A more practical approach is to select from a predefined list of values, similar to how set variables work but returning a single value instead of multiple.

## What Changes

Modify the string variable type to use a `values` list instead of length parameters:

**Before:**
```python
{"type": "string", "min_length": 5, "max_length": 10}
# Generates: "xkqwp", "abcdefgh", etc.
```

**After:**
```python
{"type": "string", "values": ["products", "news", "posts", "articles"]}
# Generates: "products" or "news" or "posts" or "articles"
```

## Capabilities

### New Capabilities

_None - this modifies existing functionality_

### Modified Capabilities

- **string-variable-type**: Change from random character generation to random selection from a values list

## Impact

- **Model changes**: Update `VariableGenerator.generate_string()` to accept `values` list instead of length parameters
- **Validation changes**: Update `_validate_variable_definition()` to validate the new structure
- **Breaking change**: Existing string variables using `min_length`/`max_length` will no longer work
- **Migration**: No database migration needed (variables stored in JSONField)
- **Import command**: The YAML import already handles this format (no changes needed)
