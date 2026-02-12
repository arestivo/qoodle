## ADDED Requirements

### Requirement: State filter on template list page

Add a state filter dropdown to the template list page filter card, alongside the existing subject filter and include-sub-subjects checkbox.

#### Scenario: Filter by reviewed state
- **GIVEN** the template list page with multiple templates in different states
- **WHEN** the user selects "Reviewed" from the state filter dropdown
- **THEN** only templates with state `reviewed` are shown

#### Scenario: Filter by draft state
- **GIVEN** the template list page
- **WHEN** the user selects "Draft" from the state filter dropdown
- **THEN** only templates with state `draft` are shown

#### Scenario: No state filter (all)
- **GIVEN** the template list page
- **WHEN** the state filter is set to "All States" (default/empty value)
- **THEN** templates of all states are shown

#### Scenario: Combined subject and state filter
- **GIVEN** the template list page
- **WHEN** the user selects both a subject and a state filter
- **THEN** only templates matching both the subject and the state are shown

#### Scenario: State filter preserved in pagination
- **GIVEN** the template list with state filter active and multiple pages
- **WHEN** the user navigates to the next page
- **THEN** the state filter is preserved in the pagination URL query parameters

### UI Specification

- Add a `<select>` with `form-select` class and `name="state"` to the filter form in `question_list.html`
- Options: "-- All States --" (empty value), "Draft", "Completed", "Reviewed"
- The dropdown submits the form on change (same behavior as subject filter)
- The "Clear Filter" link clears both subject and state filters
- The selected state is preserved when the form is submitted
