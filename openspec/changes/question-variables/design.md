## Context

This design extends the existing multilingual question system (Spec 003) to support parametric questions through a variable system. The implementation must integrate seamlessly with:

- **Question/Choice models** with JSONField multilingual text storage
- **MultilingualTextField** form field with custom marker parsing
- **Custom JavaScript** for dynamic choice management
- **Markdown rendering** pipeline with template tags
- **Language fallback logic** for multilingual support

The variable system adds a new layer of text processing that occurs after language selection but before markdown rendering.

## Goals / Non-Goals

**Goals:**
- Enable teachers to create parametric questions with randomized values
- Support four variable types: num, string, set, expression
- Integrate variable substitution into existing rendering pipeline
- Provide user-friendly form UI for variable definition
- Validate variable definitions and text references before save
- Maintain backward compatibility with existing questions
- Achieve >80% test coverage for new functionality

**Non-Goals:**
- Quiz instance generation with saved variable values per student
- Variable sharing across multiple questions
- Complex control flow (if/else, loops) in variables
- Import/export of variable definitions
- Performance optimization for thousands of simultaneous evaluations
- Real-time variable preview as teacher types

## Decisions

### 1. Variable Storage in JSONField

Store all variable definitions in a single `variables` JSONField on the Question model.

**Structure:**
```python
variables = models.JSONField(
    null=True,
    blank=True,
    default=dict,
    help_text="Variable definitions for parametric questions"
)
```

**JSON format:**
```json
{
  "variable_name": {
    "type": "num|string|set|expression",
    "min": <number>,          // num only
    "max": <number>,          // num only
    "precision": <number>,    // num only (default: 1)
    "min_length": <int>,      // string only
    "max_length": <int>,      // string only
    "items": [<string>],      // set only
    "size": <int>,            // set only
    "formula": <string>       // expression only
  }
}
```

**Rationale:**
- Consistent with existing `text` JSONField pattern
- Allows flexible schema for different variable types
- Easily extensible for future variable types
- No additional tables/migrations needed beyond one field
- Django admin handles JSON editing out of the box

**Alternatives considered:**
- Separate Variable model with ForeignKey: Rejected due to complexity, over-engineering for this use case
- Separate fields per type (num_vars, string_vars, etc.): Rejected due to messy schema, hard to query all variables

---

### 2. Variable Evaluation Strategy

Use Python's `eval()` for expression evaluation with a controlled namespace containing only defined variables.

**Implementation:**
```python
def evaluate_expression(formula: str, variable_values: dict) -> Any:
    """Evaluate expression with only variable values in namespace."""
    try:
        # Safe built-ins: math functions, basic types
        safe_builtins = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'int': int, 'float': float, 'str': str,
            'len': len, 'sum': sum
        }
        namespace = {**safe_builtins, **variable_values}
        return eval(formula, {"__builtins__": {}}, namespace)
    except Exception as e:
        raise ValidationError(f"Expression evaluation failed: {e}")
```

**Rationale:**
- eval() is acceptable in teacher-only context (same trust level as Django admin)
- Provides maximum flexibility for mathematical expressions
- Controlled namespace prevents access to dangerous functions
- Standard Python syntax (teachers already know it)

**Alternatives considered:**
- Custom expression parser: Rejected due to complexity, limited functionality
- sympy or similar library: Rejected due to added dependency, overkill for simple arithmetic
- String template only (no evaluation): Rejected, doesn't meet requirement for computed values

---

### 3. Variable Substitution Pipeline

Integrate variable substitution into the existing text rendering flow:

**Current flow:**
```
Multilingual JSON → Language Fallback → Markdown Rendering → HTML
```

**New flow:**
```
Multilingual JSON → Language Fallback → Variable Substitution → Markdown Rendering → HTML
```

**Implementation location:** Extend `get_text()` method in Question and Choice models

```python
def get_text(self, language_code: str = None, variables: dict = None) -> str:
    """Get text with language fallback and variable substitution."""
    # Step 1: Language fallback (existing)
    text = self._get_text_for_language(language_code)
    
    # Step 2: Variable substitution (NEW)
    if variables:
        text = self._substitute_variables(text, variables)
    
    return text

def _substitute_variables(self, text: str, variables: dict) -> str:
    """Replace {{var}} and {{expression}} with evaluated values."""
    import re
    
    def replacer(match):
        expression = match.group(1).strip()
        try:
            return str(eval(expression, {"__builtins__": {}}, variables))
        except Exception as e:
            return f"{{{{ERROR: {e}}}}}"
    
    return re.sub(r'\{\{(.+?)\}\}', replacer, text)
```

**Rationale:**
- Minimal changes to existing code
- Variable substitution is optional (backward compatible)
- Happens before markdown, so {{a + b}} evaluates then markdown processes result
- Clear separation of concerns

---

### 4. Variable Generation with Random Seed

Support both random and seeded variable generation for preview vs. testing.

**Implementation:**
```python
def generate_variables(self, seed: int = None) -> dict:
    """Generate random values for all variables."""
    import random
    if seed is not None:
        random.seed(seed)
    
    values = {}
    # Topologically sort variables to handle dependencies
    sorted_vars = self._topological_sort_variables()
    
    for var_name in sorted_vars:
        var_def = self.variables[var_name]
        values[var_name] = self._generate_variable_value(var_def, values)
    
    return values
```

**Rationale:**
- Seed support enables reproducible testing
- No seed gives random preview instances
- Topological sort ensures expression variables evaluate after dependencies

---

### 5. Validation Strategy

Validate variable definitions and text references on Question model save.

**Validation points:**
1. **clean()** method: Validate variable definitions structure
2. **clean()** method: Detect circular dependencies
3. **clean()** method: Validate text references
4. **clean()** method: Test-evaluate expressions with sample data

```python
def clean(self):
    """Validate variable definitions and text references."""
    super().clean()
    
    if not self.variables:
        return
    
    # Validate each variable definition
    for name, var_def in self.variables.items():
        self._validate_variable_definition(name, var_def)
    
    # Check for circular dependencies
    self._validate_no_circular_dependencies()
    
    # Validate text references
    self._validate_text_references()
    
    # Test-evaluate expressions
    self._test_evaluate_expressions()
```

**Rationale:**
- Fail fast at save time, not at render time
- Provides clear error messages to teachers
- Prevents invalid questions from being saved

---

### 6. Form UI with Dynamic Fields

Use JavaScript to show/hide type-specific fields based on selected variable type.

**Form structure:**
- Variable management section with "Add Variable" button
- Each variable row has: name input, type dropdown, type-specific fields, remove button
- Type-specific fields shown/hidden via JavaScript based on type selection

**Template:** `apps/questions/templates/questions/question_form.html`

**JavaScript:** `apps/questions/static/questions/js/variable_form.js`

**Bootstrap components:**
- Card for variable section
- Input groups for variable rows
- Collapse for type-specific field groups
- Buttons with FontAwesome icons (fa-plus, fa-trash)

**Rationale:**
- Consistent with existing choice management UI pattern
- Bootstrap provides responsive, accessible components
- JavaScript deferred loading (no DOMContentLoaded wrapper needed)

---

### 7. Preview Implementation

Add "Variable Preview" section to QuestionPreviewView showing multiple random instances.

**Implementation:**
- Generate 3-5 random instances with different seeds
- Display each instance in a Bootstrap card
- Show variable values used for each instance
- "Regenerate" button to create new instances

**Template section:**
```django
<div class="card mt-4">
  <div class="card-header">
    <h5>Variable Preview</h5>
  </div>
  <div class="card-body">
    {% for instance in preview_instances %}
      <div class="card mb-3">
        <div class="card-header">
          Instance {{ forloop.counter }}
          <small class="text-muted">
            {% for var, value in instance.variables.items %}
              {{ var }}={{ value }}{% if not forloop.last %}, {% endif %}
            {% endfor %}
          </small>
        </div>
        <div class="card-body">
          {{ instance.text|markdown }}
          <ul>
            {% for choice in instance.choices %}
              <li>{{ choice.text|markdown }}</li>
            {% endfor %}
          </ul>
        </div>
      </div>
    {% endfor %}
  </div>
</div>
```

**Rationale:**
- Allows teachers to verify variable behavior before finalizing
- Shows edge cases (min/max values, different combinations)
- Reuses existing markdown filter

---

### 8. Database Migration Strategy

Single migration adds `variables` JSONField to Question model.

**Migration file:** `apps/questions/migrations/000X_add_variables.py`

**Migration operations:**
```python
operations = [
    migrations.AddField(
        model_name='question',
        name='variables',
        field=models.JSONField(
            blank=True,
            default=dict,
            help_text='Variable definitions for parametric questions',
            null=True
        ),
    ),
]
```

**Rationale:**
- Nullable field requires no data migration
- Existing questions get null/empty dict (backward compatible)
- Simple, low-risk migration

---

### 9. Template Tag vs Model Method

Keep variable substitution in model methods, not template tags.

**Decision:** Implement in `Question.get_text(variables=...)` and `Choice.get_text(variables=...)`

**Usage in templates:**
```django
{# Generate variables first #}
{% with variables=question.generate_variables %}
  {{ question.get_text|get_item:lang|substitute_vars:variables|markdown }}
{% endwith %}
```

Actually, **better approach:** Provide `render_text()` convenience method:

```python
def render_text(self, language_code: str = None, seed: int = None) -> str:
    """Render text with variables and markdown in one call."""
    variables = self.generate_variables(seed) if self.variables else {}
    text = self.get_text(language_code, variables)
    return markdown_lib.markdown(text, extensions=[...])
```

**Template usage:**
```django
{{ question.render_text:lang }}
```

**Rationale:**
- Cleaner template syntax
- Encapsulates the full rendering pipeline
- Easy to add caching later if needed

---

### 10. URL Routing

No new URLs needed. Variables integrate into existing question views.

**Existing URLs remain:**
```python
path('', QuestionListView.as_view(), name='list'),
path('create/', QuestionCreateView.as_view(), name='create'),
path('<uuid:pk>/', QuestionPreviewView.as_view(), name='preview'),
path('<uuid:pk>/edit/', QuestionUpdateView.as_view(), name='edit'),
path('<uuid:pk>/delete/', QuestionDeleteView.as_view(), name='delete'),
```

**Changes to views:**
- **QuestionCreateView/UpdateView:** Handle variable form data in POST
- **QuestionPreviewView:** Generate and pass preview instances to template

**Rationale:**
- Variables are a feature of questions, not a separate resource
- No need for variable-specific CRUD endpoints

---

## Implementation Structure

### Models
**File:** `apps/questions/models.py`

**Changes:**
```python
class Question(UUIDModel):
    # ... existing fields ...
    variables = models.JSONField(null=True, blank=True, default=dict)
    
    def generate_variables(self, seed=None) -> dict: ...
    def _generate_variable_value(self, var_def, context) -> Any: ...
    def _substitute_variables(self, text, variables) -> str: ...
    def _validate_variable_definition(self, name, var_def): ...
    def _validate_no_circular_dependencies(self): ...
    def _validate_text_references(self): ...
    def _topological_sort_variables(self) -> list: ...
    def render_text(self, language_code=None, seed=None) -> str: ...
```

**Helper classes:**
```python
class VariableGenerator:
    """Handles variable value generation for different types."""
    @staticmethod
    def generate_num(min_val, max_val, precision=1): ...
    @staticmethod
    def generate_string(min_len, max_len): ...
    @staticmethod
    def generate_set(items, size): ...
    @staticmethod
    def evaluate_expression(formula, context): ...
```

### Forms
**File:** `apps/questions/forms.py`

**Changes:**
```python
class QuestionForm(forms.ModelForm):
    # ... existing fields ...
    variables_json = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Variable definitions (managed by JavaScript)"
    )
    
    def clean_variables_json(self): ...
    def save(self, commit=True): ...
```

### Views
**File:** `apps/questions/views.py`

**Changes:**
```python
class QuestionCreateView(CreateView):
    def form_valid(self, form):
        # Parse variables from form data
        variables = self._parse_variable_form_data(self.request.POST)
        form.instance.variables = variables
        return super().form_valid(form)

class QuestionPreviewView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.variables:
            context['preview_instances'] = [
                {
                    'variables': self.object.generate_variables(seed=i),
                    'text': self.object.render_text(seed=i),
                    'choices': [
                        {'text': choice.render_text(seed=i)}
                        for choice in self.object.choices.all()
                    ]
                }
                for i in range(3)
            ]
        return context
```

### Templates
**File:** `apps/questions/templates/questions/question_form.html`

**New section:**
```django
<div class="card mt-4" id="variables-section">
  <div class="card-header">
    <h5>Variables (Optional)</h5>
  </div>
  <div class="card-body">
    <div id="variable-list"></div>
    <button type="button" class="btn btn-sm btn-secondary" id="add-variable-btn">
      <i class="fas fa-plus"></i> Add Variable
    </button>
  </div>
</div>

<template id="variable-row-template">
  <div class="card mb-3 variable-row">
    <div class="card-body">
      <div class="row">
        <div class="col-md-3">
          <input type="text" class="form-control variable-name" placeholder="Variable name">
        </div>
        <div class="col-md-3">
          <select class="form-select variable-type">
            <option value="num">Number</option>
            <option value="string">String</option>
            <option value="set">Set</option>
            <option value="expression">Expression</option>
          </select>
        </div>
        <div class="col-md-5 variable-fields">
          <!-- Type-specific fields inserted here by JavaScript -->
        </div>
        <div class="col-md-1">
          <button type="button" class="btn btn-sm btn-danger remove-variable">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

### JavaScript
**File:** `apps/questions/static/questions/js/variable_form.js`

**Functions:**
```javascript
function addVariable() { ... }
function removeVariable(element) { ... }
function updateVariableFields(typeSelect) { ... }
function serializeVariables() { ... }
function loadVariables(variablesJson) { ... }

// Type-specific field templates
const fieldTemplates = {
  num: '<input type="number" class="form-control" name="min" placeholder="Min">...',
  string: '<input type="number" class="form-control" name="min_length" placeholder="Min Length">...',
  set: '<textarea class="form-control" name="items" placeholder="Items (one per line)"></textarea>...',
  expression: '<textarea class="form-control" name="formula" placeholder="Python expression"></textarea>'
};
```

### Static Files
**Location:** `apps/questions/static/questions/js/variable_form.js`

**Dependencies:** None (vanilla JavaScript, Bootstrap 5.3.8 already loaded)

### Tests
**File:** `apps/questions/tests.py`

**New test classes:**
```python
class TestVariableGeneration:
    def test_generate_num_variable()
    def test_generate_string_variable()
    def test_generate_set_variable()
    def test_generate_expression_variable()

class TestVariableSubstitution:
    def test_simple_variable_substitution()
    def test_expression_evaluation()
    def test_multiple_variables()

class TestVariableValidation:
    def test_circular_dependency_detection()
    def test_undefined_variable_reference()
    def test_invalid_expression_syntax()

class TestVariableForm:
    def test_save_question_with_variables()
    def test_validate_variable_definitions()
```

## Risks / Trade-offs

### Risk: eval() Security
**Description:** Using eval() could allow arbitrary code execution if variable context is compromised.

**Mitigation:**
- Restricted namespace (no __builtins__ access to dangerous functions)
- Only teachers can define variables (same trust level as Django admin)
- Expression length limit (200 characters)
- Document that expressions should not contain sensitive data

**Trade-off:** Accept eval() risk for flexibility vs. implement limited custom parser

---

### Risk: Performance with Complex Expressions
**Description:** Deeply nested expressions or many variables could slow rendering.

**Mitigation:**
- Expression length limit prevents extremely complex formulas
- Cache variable values during single render (evaluate once, use many times)
- Monitor performance in production, optimize if needed

**Trade-off:** Simplicity now vs. premature optimization

---

### Risk: Floating Point Precision
**Description:** Binary floating point representation causes precision issues (0.1 + 0.2 = 0.30000000000000004).

**Mitigation:**
- Round results to specified precision after generation/evaluation
- Document precision behavior in help text
- Use Python's Decimal for currency if needed (future enhancement)

**Trade-off:** Accept standard float limitations vs. add Decimal complexity

---

### Risk: Variable UI Complexity
**Description:** Managing many variables with different types could become unwieldy in the UI.

**Mitigation:**
- Keep UI simple with collapsible cards
- Show only relevant fields for each type
- Add "Variable Summary" section showing all defined vars
- Consider pagination/search if >10 variables (future enhancement)

**Trade-off:** Simple implementation now vs. advanced UI later

---

### Risk: Circular Dependency Detection Performance
**Description:** Topological sort could be slow with many interdependent variables.

**Mitigation:**
- Typical questions have <10 variables (low risk)
- Validation happens at save time (not render time, acceptable delay)
- Could optimize with memoization if needed

**Trade-off:** Correctness over speed for validation logic

---

### Trade-off: Variable Substitution Before vs. After Markdown
**Decision:** Substitute variables BEFORE markdown rendering.

**Rationale:**
- Allows {{var}} to contain markdown syntax (e.g., **bold**, _italic_)
- Teachers can use variables in markdown tables, lists, etc.
- More flexible and powerful

**Alternative:** Substitute after markdown → Rejected, limits flexibility

---

### Trade-off: JSONField vs. Separate Tables
**Decision:** Use single JSONField for all variable definitions.

**Benefits:**
- Simpler schema, fewer migrations
- Easier to extend with new variable types
- Consistent with existing `text` field pattern

**Drawbacks:**
- Less structured than normalized tables
- Harder to query variables across questions
- No database-level constraints on JSON structure

**Mitigation:** App-level validation compensates for lack of DB constraints
