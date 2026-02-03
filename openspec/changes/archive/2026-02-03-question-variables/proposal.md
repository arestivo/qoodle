# Question Variables System

## Why

Currently, questions in Qoodle are static - every student sees the exact same question text and choices. This limits the pedagogical value since students can share answers and there's no variation in practice exercises. Adding a variable system allows teachers to create parametric questions where values change for each instance, making it possible to generate thousands of unique question variations from a single template.

This is particularly valuable for subjects requiring numerical calculations (mathematics, physics, chemistry) and scenarios requiring randomized datasets (programming, statistics, data analysis).

## What Changes

Add a comprehensive variable system to the Question model that supports four variable types:
- **num**: Numeric variables with min/max bounds and precision control
- **string**: String variables with length constraints
- **set**: Random selection from predefined string sets
- **expression**: Computed values based on other variables using Python eval()

Variables will be defined per question and can be referenced in both question text and choice text using `{{variable_name}}` delimiter syntax. The system will evaluate expressions within delimiters (e.g., `{{a + b}}`) to compute final display values.

## Context

This builds on the existing multilingual question system (Spec 003):
- Questions already use JSONField for text storage with `==lang==` markers
- The `MultilingualTextField` form field already parses custom syntax
- Choice management already has custom JavaScript for dynamic UI
- Questions already support markdown rendering through template tags

The variable system will integrate at the rendering layer:
1. Variables defined in new JSONField on Question model
2. Variable substitution happens during text retrieval (after language fallback)
3. Expression evaluation using Python's `eval()` (trusted teacher context)
4. Final text rendered with markdown as usual

## Capabilities

### New Capabilities
- Define variables per question with type-specific constraints
- Use `{{variable}}` syntax in question and choice text
- Evaluate expressions within delimiters (e.g., `{{a + b}}`, `{{answer / 2}}`)
- Generate random variable values within defined constraints:
  - **num**: Random float/int between min/max with specified precision
  - **string**: Random string of length between min/max characters
  - **set**: Random subset of specified size from predefined items
  - **expression**: Computed from other variables using Python expressions
- Preview questions with sample variable substitutions
- Validate variable definitions (type constraints, expression dependencies)
- Validate references in text (all variables used are defined)

### Modified Capabilities
- **Question text rendering**: Will resolve variables before markdown rendering
- **Choice text rendering**: Will resolve variables before markdown rendering
- **Question preview**: Will show sample instances with different variable values
- **Question form**: Will add variable definition UI with type-specific fields

## Impact

**Database Changes:**
- Add `variables` JSONField to Question model
- Migration required (no data migration needed for existing questions)

**Form Changes:**
- Extend QuestionForm to include variable definition fields
- Add JavaScript for dynamic variable type-specific input fields
- Validation for variable definitions and text references

**Rendering Changes:**
- Modify `get_text()` method on Question/Choice models to resolve variables
- Variable resolution happens after language fallback, before markdown
- Template preview needs to generate sample variable values

**Testing Impact:**
- Existing question tests remain valid (variables optional)
- Need comprehensive tests for each variable type
- Need tests for expression evaluation
- Need tests for variable validation

**Performance Impact:**
- Variable evaluation happens at render time (not stored)
- Expression eval() has some overhead but acceptable for teacher-use context
- No impact on questions without variables

**Backward Compatibility:**
- Fully backward compatible (variables are optional)
- Existing questions work without modification
- Empty/null variables field treated as "no variables"

**Security Considerations:**
- `eval()` is used but acceptable in trusted teacher context
- Teachers already have admin access and can execute arbitrary Python
- Variable expressions limited to question scope (no system access)
- Consider adding expression complexity limits (character count, depth)

**Dependencies:**
- No new Python packages required (eval, json, random are built-in)
- Django 6.0.1 JSONField already available
- No frontend dependencies (vanilla JavaScript)

## Risks

1. **Circular Dependencies**: Expression variables could reference each other in circles
   - Mitigation: Topological sort of variable dependency graph during validation
   - Detect cycles and show error with variable chain

2. **Expression Evaluation Errors**: `eval()` could raise exceptions
   - Mitigation: Wrap eval in try/except, show meaningful error messages
   - Validate expressions during question save (attempt evaluation with sample values)
   - Provide clear error messages indicating which variable/expression failed

3. **Type Coercion Issues**: Mixing numbers and strings in expressions
   - Mitigation: Document best practices (use `str(var)` for concatenation)
   - Show warnings in preview if type mismatches occur

4. **Performance with Complex Expressions**: Deeply nested expressions could be slow
   - Mitigation: Limit expression length (e.g., 200 characters)
   - Cache evaluated values during single render

5. **Variable Reference Typos**: Teacher references undefined variable `{{abc}}` in text
   - Mitigation: Validate all `{{...}}` references exist in variable definitions
   - Show error on question save with list of undefined variables

6. **Precision Edge Cases**: Floating point precision issues (0.1 + 0.2 = 0.30000000000000004)
   - Mitigation: Use `round()` with specified precision after evaluation
   - Document precision behavior in help text

## Success Criteria

1. Teachers can create questions with numeric variables and see them substituted
2. Teachers can create questions with string/set variables
3. Teachers can use expressions like `{{a + b}}` in question/choice text
4. Preview shows multiple random instances of the same question
5. Validation prevents invalid variable definitions (min > max, circular deps)
6. Validation prevents undefined variable references in text
7. Existing questions continue to work without modification
8. Test coverage >80% for variable system
9. Documentation includes examples for each variable type

## Out of Scope

- Quiz instance generation (storing specific variable values per student)
- Variable sharing across questions
- Complex variable types (lists, dictionaries, objects)
- Conditional variable logic (if/else in variable definitions)
- Variable value history/logging
- Import/export of variable definitions
- Moodle XML export with variables (future enhancement)
