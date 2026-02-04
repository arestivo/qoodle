# Specification: Grading Mode Selection

## Overview

Allow teachers to select grading mode (single-choice vs multiple-choice) at exam level. This controls how answer fractions are calculated during Moodle XML export and enables different assessment strategies.

## Purpose

- Enable traditional single-choice exams (one correct answer)
- Support multiple-choice with custom fraction schemes for answer pattern tracking
- Provide clear UI for selecting and understanding grading modes
- Display grading mode information on exam detail pages

## Data Models

### Location
`apps/exams/models.py`

### Modified: Exam Model

```python
class Exam(UUIDModel):
    """An exam composed of ordered question pools."""
    
    GRADING_MODE_CHOICES = [
        ('single', 'Single Choice'),
        ('multi', 'Multiple Choice'),
    ]
    
    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    grading_mode = models.CharField(
        max_length=10,
        choices=GRADING_MODE_CHOICES,
        default='single',
        help_text=(
            "Single Choice: Traditional mode with one correct answer. "
            "Multiple Choice: Custom fractions for answer pattern tracking."
        )
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_grading_mode_display_verbose(self) -> str:
        """Get detailed grading mode description."""
        if self.grading_mode == 'single':
            return "Single Choice (One correct answer, negative fractions)"
        return "Multiple Choice (Pattern tracking, positive fractions)"

## Grading Mode Differences

### Single Choice Mode

Traditional single-answer questions where only one choice should be selected.

**Moodle XML Attributes:**
- `<single>true</single>` - Indicates radio button selection in Moodle
- Negative fractions for wrong answers

**Fraction Calculation:**
Correct answer always gets 100%, wrong answers get negative fractions based on count:

| Total Choices | Correct Fraction | Wrong Fraction | Formula |
|---------------|------------------|----------------|----------|
| 2 | 100% | -100% | -100/(n-1) |
| 3 | 100% | -50% | -100/(n-1) |
| 4 | 100% | -33.33% | -100/(n-1) |
| 5 | 100% | -25% | -100/(n-1) |
| 6 | 100% | -20% | -100/(n-1) |

**Rationale:** Negative fractions penalize students for selecting wrong answers. The penalty is proportional to the number of wrong choices available.

### Multiple Choice Mode

Allows multiple answer selection with custom positive fractions for Excel-based answer pattern analysis.

**Moodle XML Attributes:**
- `<single>false</single>` - Indicates checkbox selection in Moodle
- Positive fractions for both correct and wrong answers

**Fraction Schemes (2-6 choices):**

| Total Choices | Correct Fraction | Wrong Fraction | Score Interpretation |
|---------------|------------------|----------------|---------------------|
| 2 | 90% | 10% | 100% = all selected |
| 3 | 80% | 10% | 100% = all selected |
| 4 | 70% | 10% | 100% = all selected |
| 5 | 60% | 10% | 100% = all selected |
| 6 | 75% | 5% | 100% = all selected |

**Rationale:** Positive fractions allow teachers to export Moodle results to Excel and calculate unique scores based on answer patterns. For example, with 4 choices (70/10 scheme):
- Score 100% = correct + 3 wrong (student selected all)
- Score 90% = correct + 2 wrong
- Score 80% = correct + 1 wrong
- Score 70% = correct only (ideal answer)
- Score 30% = 3 wrong only
- Score 20% = 2 wrong only
- Score 10% = 1 wrong only

This enables sophisticated analysis of student confidence and guessing patterns.
```

## ADDED Requirements

### Requirement: Grading Mode Field in Exam Form

Display grading mode selection with clear descriptions in exam create/edit forms.

#### Form Field Configuration
- **Field Type:** RadioSelect widget
- **Choices:** Single Choice, Multiple Choice
- **Default:** Single Choice
- **Layout:** Vertical radio buttons with descriptive labels
- **Help Text:** Explain difference between modes

#### Scenario: Create exam with single-choice mode
- **GIVEN** teacher navigates to `/exams/create/`
- **WHEN** form loads
- **THEN** "Single Choice" radio button is selected by default
- **AND** help text explains: "Traditional mode (one correct answer, -33% penalty)"

#### Scenario: Create exam with multi-choice mode
- **GIVEN** teacher is on exam create form
- **WHEN** teacher selects "Multiple Choice" radio button
- **THEN** help text explains: "Custom fractions for answer pattern tracking (70/10 to 75/5)"
- **AND** form is valid when submitted

#### Scenario: Change grading mode on existing exam
- **GIVEN** existing exam with grading_mode="single"
- **WHEN** teacher edits exam and changes to "Multiple Choice"
- **AND** saves form
- **THEN** exam.grading_mode is updated to "multi"
- **AND** change is reflected in exports

### Requirement: Grading Mode Display

Show grading mode information on exam detail page.

#### Display Location
Exam detail page header, below title and date.

#### Display Format
Badge with icon:
- Single Choice: Blue badge with `<i class="fas fa-check-circle"></i>` icon
- Multiple Choice: Green badge with `<i class="fas fa-tasks"></i>` icon

#### Scenario: View single-choice exam detail
- **GIVEN** exam with grading_mode="single"
- **WHEN** teacher views exam detail page
- **THEN** page displays blue badge: "Single Choice"
- **AND** badge has check-circle icon

#### Scenario: View multi-choice exam detail
- **GIVEN** exam with grading_mode="multi"
- **WHEN** teacher views exam detail page
- **THEN** page displays green badge: "Multiple Choice"
- **AND** badge has tasks icon

### Requirement: Default Grade Field in Pool Management

Allow teachers to set point value for each question pool.

#### Field Configuration
- **Field Type:** DecimalField
- **Max Digits:** 5
- **Decimal Places:** 2
- **Default:** 1.0
- **Min Value:** 0.1
- **Validation:** Must be positive decimal

#### Display in Pool List
Show default_grade next to pool order on exam detail page:
```
Pool 1 (1.0 points)
  ├─ Template: "HTML Basics" (3 versions)
  └─ Template: "CSS Selectors" (2 versions)
```

#### Scenario: Create pool with default grade
- **GIVEN** exam detail page
- **WHEN** teacher clicks "Add Pool"
- **THEN** new pool is created with default_grade=1.0
- **AND** pool displays "(1.0 points)" label

#### Scenario: Update pool default grade
- **GIVEN** existing pool with default_grade=1.0
- **WHEN** teacher clicks edit icon next to pool
- **AND** changes default_grade to 2.5
- **AND** saves changes
- **THEN** pool displays "(2.5 points)"
- **AND** Moodle export uses 2.5 in `<defaultgrade>` tag

#### Scenario: Validate minimum default grade
- **GIVEN** pool edit form
- **WHEN** teacher enters default_grade=0.0
- **AND** submits form
- **THEN** form shows validation error: "Ensure this value is greater than or equal to 0.1"

## UI Components

### Location
`apps/exams/templates/exams/`

### Template: exam_form.html (Modified)

Add grading mode section to form:

```html
{% extends "common/base.html" %}

{% block content %}
<div class="container mt-4">
  <h1>{% if form.instance.pk %}Edit{% else %}Create{% endif %} Exam</h1>
  
  <form method="post" class="mt-4">
    {% csrf_token %}
    
    <!-- Title Field -->
    <div class="mb-3">
      <label for="id_title" class="form-label">Title</label>
      {{ form.title }}
      {% if form.title.errors %}
        <div class="invalid-feedback d-block">{{ form.title.errors }}</div>
      {% endif %}
    </div>
    
    <!-- Date Field -->
    <div class="mb-3">
      <label for="id_date" class="form-label">Date (Optional)</label>
      {{ form.date }}
    </div>
    
    <!-- Description Field -->
    <div class="mb-3">
      <label for="id_description" class="form-label">Description (Optional)</label>
      {{ form.description }}
    </div>
    
    <!-- Grading Mode Field -->
    <div class="mb-4">
      <label class="form-label fw-bold">Grading Mode</label>
      <div class="form-text mb-2">
        Choose how answer fractions are calculated during Moodle export.
      </div>
      
      <div class="form-check mb-2">
        <input class="form-check-input" type="radio" 
               name="grading_mode" id="grading_single" value="single"
               {% if form.grading_mode.value == 'single' or not form.grading_mode.value %}checked{% endif %}>
        <label class="form-check-label" for="grading_single">
          <strong><i class="fas fa-check-circle text-primary"></i> Single Choice</strong>
          <div class="text-muted small">
            Traditional mode: Correct answer = 100%, Wrong answers = -33.33%
          </div>
        </label>
      </div>
      
      <div class="form-check">
        <input class="form-check-input" type="radio" 
               name="grading_mode" id="grading_multi" value="multi"
               {% if form.grading_mode.value == 'multi' %}checked{% endif %}>
        <label class="form-check-label" for="grading_multi">
          <strong><i class="fas fa-tasks text-success"></i> Multiple Choice</strong>
          <div class="text-muted small">
            Excel tracking mode: Custom fractions (70/10 for 4 choices, 75/5 for 6 choices) 
            to analyze answer patterns
          </div>
        </label>
      </div>
      
      {% if form.grading_mode.errors %}
        <div class="invalid-feedback d-block">{{ form.grading_mode.errors }}</div>
      {% endif %}
    </div>
    
    <!-- Submit Buttons -->
    <div class="d-flex gap-2">
      <button type="submit" class="btn btn-primary">
        <i class="fas fa-save"></i> Save
      </button>
      <a href="{% url 'exams:list' %}" class="btn btn-secondary">
        Cancel
      </a>
    </div>
  </form>
</div>
{% endblock %}
```

### Template: exam_detail.html (Modified)

Display grading mode badge:

```html
{% extends "common/base.html" %}

{% block content %}
<div class="container mt-4">
  <!-- Header with Grading Mode Badge -->
  <div class="mb-3">
    <h1>{{ exam.title }}</h1>
    <div class="d-flex align-items-center gap-2 mt-2">
      {% if exam.date %}
        <span class="text-muted">
          <i class="fas fa-calendar"></i> {{ exam.date|date:"Y-m-d" }}
        </span>
      {% endif %}
      
      <!-- Grading Mode Badge -->
      {% if exam.grading_mode == 'single' %}
        <span class="badge bg-primary">
          <i class="fas fa-check-circle"></i> Single Choice
        </span>
      {% else %}
        <span class="badge bg-success">
          <i class="fas fa-tasks"></i> Multiple Choice
        </span>
      {% endif %}
    </div>
  </div>
  
  <!-- Rest of exam detail content -->
  {% if exam.description %}
    <div class="alert alert-info">
      {{ exam.description }}
    </div>
  {% endif %}
  
  <!-- Pools List -->
  <h2 class="mt-4">Question Pools</h2>
  {% for pool in exam.pools.all %}
    <div class="card mb-3">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>
          <strong>Pool {{ pool.order }}</strong>
          <span class="badge bg-secondary">{{ pool.default_grade }} points</span>
        </span>
        <div class="btn-group btn-group-sm">
          <button class="btn btn-outline-secondary" data-bs-toggle="modal" 
                  data-bs-target="#editPoolModal{{ pool.pk }}">
            <i class="fas fa-edit"></i> Edit Grade
          </button>
          <button class="btn btn-outline-danger">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
      <div class="card-body">
        <!-- Pool templates -->
      </div>
    </div>
  {% empty %}
    <p class="text-muted">No pools yet. Add your first pool to get started.</p>
  {% endfor %}
</div>

<!-- Edit Pool Modal -->
{% for pool in exam.pools.all %}
<div class="modal fade" id="editPoolModal{{ pool.pk }}" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Edit Pool {{ pool.order }} Grade</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form method="post" action="{% url 'exams:pool_update_grade' exam.pk pool.pk %}">
        {% csrf_token %}
        <div class="modal-body">
          <div class="mb-3">
            <label for="default_grade_{{ pool.pk }}" class="form-label">
              Default Grade (points)
            </label>
            <input type="number" class="form-control" 
                   id="default_grade_{{ pool.pk }}" 
                   name="default_grade" 
                   value="{{ pool.default_grade }}"
                   step="0.1" min="0.1" required>
            <div class="form-text">
              Point value for questions in this pool (minimum: 0.1)
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            <i class="fas fa-save"></i> Save
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
{% endfor %}
{% endblock %}
```

## Forms

### Location
`apps/exams/forms.py`

### Modified: ExamForm

```python
from django import forms
from .models import Exam

class ExamForm(forms.ModelForm):
    """Form for creating and editing exams."""
    
    class Meta:
        model = Exam
        fields = ['title', 'date', 'description', 'grading_mode']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam title'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'grading_mode': forms.RadioSelect(),
        }
```

### New: PoolGradeForm

```python
class PoolGradeForm(forms.ModelForm):
    """Form for updating pool default grade."""
    
    class Meta:
        model = QuestionPool
        fields = ['default_grade']
        widgets = {
            'default_grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1'
            })
        }
```

## Views

### Location
`apps/exams/views.py`

### New: PoolUpdateGradeView

```python
from django.views.generic import UpdateView
from django.contrib import messages

class PoolUpdateGradeView(UpdateView):
    """Update the default grade for a question pool."""
    
    model = QuestionPool
    form_class = PoolGradeForm
    
    def get_success_url(self):
        return reverse('exams:detail', kwargs={'pk': self.object.exam.pk})
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f"Pool {self.object.order} grade updated to {form.cleaned_data['default_grade']} points"
        )
        return super().form_valid(form)
```

## Testing

### Location
`apps/exams/tests.py`

### Test Coverage

```python
class GradingModeTests(TestCase):
    """Tests for grading mode selection."""
    
    def test_exam_default_grading_mode(self):
        """Test that default grading mode is 'single'."""
        exam = Exam.objects.create(title="Test Exam")
        self.assertEqual(exam.grading_mode, 'single')
    
    def test_create_exam_with_multi_mode(self):
        """Test creating exam with multi-choice mode."""
        exam = Exam.objects.create(
            title="Test Exam",
            grading_mode='multi'
        )
        self.assertEqual(exam.grading_mode, 'multi')
    
    def test_exam_form_grading_mode_choices(self):
        """Test that exam form includes grading mode choices."""
        form = ExamForm()
        self.assertIn('grading_mode', form.fields)
        self.assertEqual(len(form.fields['grading_mode'].choices), 2)
    
    def test_pool_default_grade_default_value(self):
        """Test that pool default grade defaults to 1.0."""
        exam = Exam.objects.create(title="Test")
        pool = QuestionPool.objects.create(exam=exam, order=1)
        self.assertEqual(pool.default_grade, Decimal('1.0'))
    
    def test_pool_default_grade_validation(self):
        """Test that pool default grade must be >= 0.1."""
        exam = Exam.objects.create(title="Test")
        pool = QuestionPool(exam=exam, order=1, default_grade=0.0)
        
        with self.assertRaises(ValidationError):
            pool.full_clean()
    
    def test_update_pool_grade_view(self):
        """Test updating pool grade via view."""
        exam = Exam.objects.create(title="Test")
        pool = QuestionPool.objects.create(exam=exam, order=1, default_grade=1.0)
        
        response = self.client.post(
            reverse('exams:pool_update_grade', kwargs={
                'exam_pk': exam.pk,
                'pk': pool.pk
            }),
            {'default_grade': '2.5'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        pool.refresh_from_db()
        self.assertEqual(pool.default_grade, Decimal('2.5'))
```

## URLs

### Location
`apps/exams/urls.py`

### Added Routes

```python
urlpatterns = [
    # Existing routes...
    
    path(
        '<uuid:exam_pk>/pool/<uuid:pk>/grade/',
        PoolUpdateGradeView.as_view(),
        name='pool_update_grade'
    ),
]
```

## Dependencies

- [exam-management](../../specs/exam-management/spec.md) - Base Exam and QuestionPool models

## Related Specifications

- [moodle-xml-export](../moodle-xml-export/spec.md) - Uses grading_mode for fraction calculation
