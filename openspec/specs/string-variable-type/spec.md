## MODIFIED Requirements

### Requirement: String Variable Definition

String variables select a random value from a predefined list.

#### Scenario: Valid string variable definition
- **WHEN** a variable is defined as `{"type": "string", "values": ["a", "b", "c"]}`
- **THEN** the variable is valid
- **THEN** generation returns one of "a", "b", or "c"

#### Scenario: Empty values list
- **WHEN** a variable is defined as `{"type": "string", "values": []}`
- **THEN** validation fails with error "Variable 'name': 'values' cannot be empty"

#### Scenario: Missing values field
- **WHEN** a variable is defined as `{"type": "string"}`
- **THEN** validation fails with error "Variable 'name' missing 'values' field"

#### Scenario: Non-list values field
- **WHEN** a variable is defined as `{"type": "string", "values": "not a list"}`
- **THEN** validation fails with error "Variable 'name': 'values' must be a list"

---

### Requirement: String Variable Generation

The generator selects one random value from the values list.

#### Scenario: Random selection
- **WHEN** generating a string variable with `values: ["apple", "banana", "cherry"]`
- **THEN** one of the three values is returned
- **THEN** each value has equal probability of selection

#### Scenario: Single value list
- **WHEN** generating a string variable with `values: ["only"]`
- **THEN** "only" is always returned

#### Scenario: Reproducible with seed
- **WHEN** generating with the same seed
- **THEN** the same value is returned each time

---

### Requirement: Backward Compatibility

Old string variable format is no longer supported.

#### Scenario: Old format rejected
- **WHEN** a variable uses `{"type": "string", "min_length": 5, "max_length": 10}`
- **THEN** validation fails with error "Variable 'name' missing 'values' field"
