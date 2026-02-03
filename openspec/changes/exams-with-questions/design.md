# Design: Exam Management with Question Pools

## Context

This change introduces an exam management system to Qoodle that allows teachers to create structured assessments composed of ordered question pools. Each pool contains multiple question templates with configurable version counts, enabling Moodle to generate diverse exam variants while preventing duplicate questions.

The design builds on the existing multilingual question system with variable substitution. The core architectural decision is to rename `Question` → `QuestionTemplate` to better reflect the template-based nature of the system, then add exam/pool models on top.

**Key relationships:**
```
Exam (1) → (N) QuestionPool → (N) QuestionTemplate
```

Each QuestionPool-QuestionTemplate relationship stores `number_of_versions` to control how many variable-generated variants Moodle should create for that specific question in that specific pool.

## Goals / Non-Goals

**Goals:**
- Enable creation of structured exams with ordered question pools
- Prevent duplicate question templates within a single exam
- Provide intuitive UI for selecting and filtering question templates
- Preserve all existing question (template) functionality during rename
- Support bulk operations (add multiple templates to a pool at once)
- Maintain clean separation: exams app manages exam/pool, questions app manages templates

**Non-Goals:**
- Moodle XML export/import (out of scope for this change)
- Student-facing exam taking interface (Moodle handles this)
- Automatic question difficulty balancing across pools
- Question template versioning/revision history
- Real-time collaborative exam editing

## Decisions

### 1. Create Separate `exams` App

**Decision:** Create new `apps/exams/` app for Exam and QuestionPool models rather than adding to `apps/questions/`.

**Rationale:**
- Clear separation of concerns: questions app manages question templates, exams app manages exam structure
- Prevents circular dependencies (exams imports questions, not vice versa)
- Allows independent evolution of exam features (e.g., future exam settings, analytics)
- Follows Django best practice of focused, composable apps

**Alternatives considered:**
- **Add to questions app:** Rejected because it conflates template authoring with exam assembly
- **Create three apps (exams, pools, templates):** Rejected as over-engineered; pool is tightly coupled to exam

**Implementation:**
```bash
poetry run python manage.py startapp exams apps/exams
```

### 2. Use Through Model for Pool-Template Relationship

**Decision:** Use explicit `QuestionPoolTemplate` model instead of simple ManyToManyField.

**Rationale:**
- Need to store `number_of_versions` per pool-template pairing
- Enables validation logic (duplicate prevention) at model level
- Allows future expansion (e.g., weighting, points per question)
- Django best practice for M2M with extra data

**Model definition:**
```python
class QuestionPoolTemplate(UUIDModel):
    """Through table linking question pools to templates with version count."""
    pool = models.ForeignKey('QuestionPool', on_delete=models.CASCADE, related_name='pool_templates')
    template = models.ForeignKey('questions.QuestionTemplate', on_delete=models.CASCADE, related_name='pool_memberships')
    number_of_versions = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    class Meta:
        unique_together = [('pool', 'template')]  # Prevent duplicates in same pool
        verbose_name = 'Question Pool Template'
        verbose_name_plural = 'Question Pool Templates'
```

**Alternatives considered:**
- **Simple M2M with through_defaults:** Rejected because Django doesn't support validation on through defaults
- **Store versions in JSON on Pool:** Rejected as it loses relational integrity and queryability

### 3. Pool-Level Duplicate Prevention (Not Exam-Level)

**Decision:** Enforce unique_together on (pool, template) rather than exam-wide uniqueness.

**Rationale:**
- Simpler database constraint (single table, no cross-pool queries)
- Matches user mental model: "don't add same question twice to this pool"
- Allows same template in different pools if truly needed (edge case flexibility)
- Easier to implement and test

**UI validation:**
When selecting templates for a pool, filter out templates already in that pool. When checking exam-wide duplicates, show warnings but allow override.

**Alternatives considered:**
- **Exam-level uniqueness constraint:** Rejected because it requires complex multi-table constraints or triggers
- **No duplicate prevention:** Rejected as it's a core user requirement from proposal

### 4. QuestionPool Order Field (Not Auto-Increment)

**Decision:** Use explicit `PositiveIntegerField` for pool order, manually managed by views.

**Rationale:**
- Simple, predictable ordering for UI display and Moodle export
- Easy to reorder (swap order values)
- No need for complicated ordering libraries
- Matches Django admin's built-in ordering pattern

**Implementation:**
```python
class QuestionPool(UUIDModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='pools')
    order = models.PositiveIntegerField()
    question_templates = models.ManyToManyField(
        'questions.QuestionTemplate',
        through='QuestionPoolTemplate',
        related_name='pools'
    )
    
    class Meta:
        ordering = ['order']
        unique_together = [('exam', 'order')]
```

**Alternatives considered:**
- **Use django-ordered-model:** Rejected as it adds dependency for simple use case
- **Auto-increment with DB sequences:** Rejected because reordering is complex (requires renumbering)

### 5. Model Rename Strategy: Two-Phase Migration

**Decision:** Rename Question → QuestionTemplate using Django's `migrations.RenameModel()` in a dedicated migration, then update all code references.

**Rationale:**
- Django handles all FK updates automatically
- Preserves all existing data without manual data migration
- Atomic operation (rollback-safe)
- Standard Django pattern for model renames

**Migration sequence:**
```python
# apps/questions/migrations/000X_rename_question_to_questiontemplate.py
operations = [
    migrations.RenameModel(
        old_name='Question',
        new_name='QuestionTemplate',
    ),
]
```

**Codebase updates:**
1. Models: Update `Question` → `QuestionTemplate`, `question` FK → `template`
2. Views: Update imports, queryset references
3. Forms: Update model references, labels
4. Templates: Update variable names (keep `question` for backward compat or rename)
5. URLs: Keep paths as `/questions/` (no change)
6. Tests: Update all test references
7. Admin: Update admin class registration

**Alternatives considered:**
- **Create new model, migrate data, delete old:** Rejected as unnecessarily complex and risky
- **Keep Question name:** Rejected because it obscures the template nature

### 6. URL Structure

**Decision:** Nest pool management under exams, keep questions separate.

**URL hierarchy:**
```
/questions/                        # List question templates
/questions/create/                 # Create template
/questions/<uuid:pk>/              # View template
/questions/<uuid:pk>/edit/         # Edit template
/questions/<uuid:pk>/delete/       # Delete template

/exams/                            # List exams
/exams/create/                     # Create exam
/exams/<uuid:pk>/                  # Exam detail (shows pools)
/exams/<uuid:pk>/edit/             # Edit exam metadata
/exams/<uuid:pk>/delete/           # Delete exam
/exams/<uuid:pk>/pools/add/        # Add pool to exam
/exams/<uuid:pk>/pools/<uuid:pool_pk>/edit/        # Edit pool (reorder, add templates)
/exams/<uuid:pk>/pools/<uuid:pool_pk>/delete/      # Delete pool
```

**Rationale:**
- RESTful nesting reflects ownership (pools belong to exams)
- Clear separation of template authoring vs exam assembly
- UUID primary keys in URLs (consistent with UUIDModel)

**Alternatives considered:**
- **Flat URLs like /pools/<uuid:pk>/:** Rejected because pools have no meaning outside exam context
- **Keep /questions/ for templates:** CHOSEN to maintain URL stability (no redirects needed)

### 7. Template Inheritance Structure

**Decision:** Exams app extends common base, uses dedicated templates in `apps/exams/templates/exams/`.

**Template hierarchy:**
```
apps/common/templates/common/base.html
└─ apps/exams/templates/exams/base_exams.html (if needed)
    ├─ apps/exams/templates/exams/exam_list.html
    ├─ apps/exams/templates/exams/exam_detail.html
    ├─ apps/exams/templates/exams/exam_form.html
    └─ apps/exams/templates/exams/pool_form.html
```

**Shared components:**
- Use Bootstrap 5.3.8 for all UI (consistent with questions app)
- FontAwesome icons for actions (edit, delete, reorder)
- HTMX or vanilla JS for drag-to-reorder pools (defer decision to tasks)

**Alternatives considered:**
- **Global templates folder:** Rejected per project convention (all templates in app folders)
- **Reuse questions templates:** Rejected because exam UI is distinct from question authoring

### 8. Form Strategy for Pool Management

**Decision:** Use Django formsets for bulk adding templates to pools.

**Rationale:**
- Django formsets handle multiple template selections naturally
- Validation built-in (required fields, unique checks)
- Easy to render with Bootstrap form styling
- Standard pattern for "select many with extra data" UI

**Implementation:**
```python
# apps/exams/forms.py
from django.forms import modelformset_factory

QuestionPoolTemplateFormSet = modelformset_factory(
    QuestionPoolTemplate,
    fields=['template', 'number_of_versions'],
    extra=1,
    can_delete=True
)
```

**UI flow:**
1. Exam detail page shows pools with "Add Templates" button per pool
2. Click button → Modal or new page with checkboxes for available templates
3. For each checked template, show number_of_versions input (default: 1)
4. Submit → Formset validates and saves all QuestionPoolTemplate instances

**Alternatives considered:**
- **Custom AJAX form:** Rejected as it duplicates Django validation logic
- **Inline admin formsets:** Rejected because we need custom filtering (by subject, already-used)

### 9. Duplicate Prevention UX

**Decision:** Use three-tier duplicate prevention:

**Tier 1 - Database constraint (hard block):**
```python
unique_together = [('pool', 'template')]  # in QuestionPoolTemplate
```

**Tier 2 - Form validation (pool-level):**
```python
def clean(self):
    # In QuestionPoolTemplateFormSet
    if template already in pool.pool_templates.all():
        raise ValidationError("Template already in this pool")
```

**Tier 3 - UI filtering (exam-level warning):**
```javascript
// In template selection modal
// Show warning icon for templates already used in other pools
// But allow selection if teacher really wants it
```

**Rationale:**
- Database constraint prevents data corruption
- Form validation gives clear error messages
- UI warnings guide best practices without blocking edge cases

**Alternatives considered:**
- **Hard block at exam level:** Rejected as too restrictive (spec says pool-level uniqueness)
- **No UI warnings:** Rejected as it misses opportunity to guide users

### 10. Static File Organization

**Decision:** Each app's static files in `apps/{app}/static/{app}/`.

**Exams app static structure:**
```
apps/exams/static/exams/
├─ css/
│  └─ exams.css          # Exam-specific styles (pool ordering UI, etc.)
└─ js/
   ├─ exam_form.js       # Exam create/edit page interactions
   └─ pool_management.js # Pool ordering, template selection
```

**Questions app updates:**
```
apps/questions/static/questions/
├─ css/
│  └─ questions.css      # Already exists
└─ js/
   └─ question_form.js   # Update labels to say "Question Template"
```

**Loading strategy:**
- Use `{% load static %}` in templates
- Include app-specific CSS/JS with `defer` attribute
- No global static folder (per project conventions)

**Alternatives considered:**
- **Global static folder:** Rejected per project structure conventions
- **Single questions app for all static:** Rejected because exams and questions are separate concerns

## Database Schema

### New Models

**Exam (apps/exams/models.py):**
```python
class Exam(UUIDModel):
    """An exam composed of ordered question pools."""
    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
    
    def __str__(self):
        return self.title
```

**QuestionPool (apps/exams/models.py):**
```python
class QuestionPool(UUIDModel):
    """Ordered slot in an exam containing alternative question templates."""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='pools')
    order = models.PositiveIntegerField()
    question_templates = models.ManyToManyField(
        'questions.QuestionTemplate',
        through='QuestionPoolTemplate',
        related_name='pools'
    )
    
    class Meta:
        ordering = ['order']
        unique_together = [('exam', 'order')]
        verbose_name = 'Question Pool'
        verbose_name_plural = 'Question Pools'
    
    def __str__(self):
        return f"{self.exam.title} - Pool {self.order}"
```

**QuestionPoolTemplate (apps/exams/models.py):**
```python
from django.core.validators import MinValueValidator

class QuestionPoolTemplate(UUIDModel):
    """Through table linking pools to templates with version count."""
    pool = models.ForeignKey(QuestionPool, on_delete=models.CASCADE, related_name='pool_templates')
    template = models.ForeignKey('questions.QuestionTemplate', on_delete=models.CASCADE, related_name='pool_memberships')
    number_of_versions = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    class Meta:
        unique_together = [('pool', 'template')]
        verbose_name = 'Question Pool Template'
        verbose_name_plural = 'Question Pool Templates'
    
    def __str__(self):
        return f"{self.pool} - {self.template.title} (x{self.number_of_versions})"
```

### Renamed Model

**QuestionTemplate (apps/questions/models.py):**
```python
# Renamed from Question
class QuestionTemplate(UUIDModel):
    """
    A question template that can generate multiple question instances
    through variable substitution.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='question_templates')
    title = models.CharField(max_length=255)
    text = models.JSONField()  # Multilingual: {lang_code: text}
    variables = models.JSONField(default=list, blank=True)
    validation_rules = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ... (rest unchanged)
```

**Choice (apps/questions/models.py):**
```python
# Update foreign key field name
class Choice(UUIDModel):
    template = models.ForeignKey(  # RENAMED from 'question'
        QuestionTemplate,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.JSONField()
    order = models.PositiveIntegerField()
    
    # ... (rest unchanged)
```

### Migrations

**Migration 1 - Rename Question:**
```python
# apps/questions/migrations/000X_rename_question_to_questiontemplate.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('questions', '000Y_previous_migration'),
    ]
    
    operations = [
        migrations.RenameModel(
            old_name='Question',
            new_name='QuestionTemplate',
        ),
    ]
```

**Migration 2 - Rename Choice FK:**
```python
# apps/questions/migrations/000X+1_rename_choice_question_to_template.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('questions', '000X_rename_question_to_questiontemplate'),
    ]
    
    operations = [
        migrations.RenameField(
            model_name='choice',
            old_name='question',
            new_name='template',
        ),
    ]
```

**Migration 3 - Create Exams App:**
```python
# apps/exams/migrations/0001_initial.py
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('questions', '000X+1_rename_choice_question_to_template'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('date', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QuestionPool',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('order', models.PositiveIntegerField()),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pools', to='exams.exam')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('exam', 'order')},
            },
        ),
        migrations.CreateModel(
            name='QuestionPoolTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('number_of_versions', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('pool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pool_templates', to='exams.questionpool')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pool_memberships', to='questions.questiontemplate')),
            ],
            options={
                'unique_together': {('pool', 'template')},
            },
        ),
        migrations.AddField(
            model_name='questionpool',
            name='question_templates',
            field=models.ManyToManyField(related_name='pools', through='exams.QuestionPoolTemplate', to='questions.QuestionTemplate'),
        ),
    ]
```

## URL Routing

### Exams App URLs

**apps/exams/urls.py:**
```python
from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # Exam CRUD
    path('', views.ExamListView.as_view(), name='list'),
    path('create/', views.ExamCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.ExamDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.ExamUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.ExamDeleteView.as_view(), name='delete'),
    
    # Pool Management
    path('<uuid:exam_pk>/pools/add/', views.PoolCreateView.as_view(), name='pool_create'),
    path('<uuid:exam_pk>/pools/<uuid:pk>/edit/', views.PoolUpdateView.as_view(), name='pool_edit'),
    path('<uuid:exam_pk>/pools/<uuid:pk>/delete/', views.PoolDeleteView.as_view(), name='pool_delete'),
    path('<uuid:exam_pk>/pools/<uuid:pk>/reorder/', views.PoolReorderView.as_view(), name='pool_reorder'),
    
    # Template Selection for Pool
    path('<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/add/', views.PoolTemplateAddView.as_view(), name='pool_template_add'),
    path('<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/<uuid:pk>/delete/', views.PoolTemplateDeleteView.as_view(), name='pool_template_delete'),
]
```

**Project-level urls.py update:**
```python
# qoodle/urls.py
urlpatterns = [
    # ... existing patterns
    path('questions/', include('apps.questions.urls')),  # Keep as-is (no URL change)
    path('exams/', include('apps.exams.urls')),  # NEW
]
```

## View Architecture

### Exams App Views

**apps/exams/views.py:**
```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import Exam, QuestionPool, QuestionPoolTemplate
from .forms import ExamForm, QuestionPoolForm, QuestionPoolTemplateFormSet

class ExamListView(ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 20

class ExamDetailView(DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch pools with templates for efficiency
        context['pools'] = self.object.pools.prefetch_related('pool_templates__template')
        return context

class ExamCreateView(CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:detail', kwargs={'pk': self.object.pk})

class ExamUpdateView(UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:detail', kwargs={'pk': self.object.pk})

class ExamDeleteView(DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exams:list')

class PoolCreateView(CreateView):
    model = QuestionPool
    form_class = QuestionPoolForm
    template_name = 'exams/pool_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        return context
    
    def form_valid(self, form):
        exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        form.instance.exam = exam
        # Set order to max+1
        max_order = exam.pools.aggregate(models.Max('order'))['order__max'] or 0
        form.instance.order = max_order + 1
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('exams:detail', kwargs={'pk': self.kwargs['exam_pk']})

class PoolUpdateView(UpdateView):
    model = QuestionPool
    form_class = QuestionPoolForm
    template_name = 'exams/pool_form.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:detail', kwargs={'pk': self.kwargs['exam_pk']})

class PoolDeleteView(DeleteView):
    model = QuestionPool
    template_name = 'exams/pool_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('exams:detail', kwargs={'pk': self.kwargs['exam_pk']})

class PoolTemplateAddView(CreateView):
    """Add multiple question templates to a pool using formset."""
    model = QuestionPoolTemplate
    template_name = 'exams/pool_template_add.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pool = get_object_or_404(QuestionPool, pk=self.kwargs['pool_pk'])
        exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        
        context['exam'] = exam
        context['pool'] = pool
        
        # Get available templates (filter by subject if needed)
        # Exclude templates already in this pool
        existing_template_ids = pool.pool_templates.values_list('template_id', flat=True)
        context['available_templates'] = QuestionTemplate.objects.exclude(
            id__in=existing_template_ids
        ).select_related('subject')
        
        if self.request.POST:
            context['formset'] = QuestionPoolTemplateFormSet(self.request.POST)
        else:
            context['formset'] = QuestionPoolTemplateFormSet(queryset=QuestionPoolTemplate.objects.none())
        
        return context
    
    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(QuestionPool, pk=self.kwargs['pool_pk'])
        formset = QuestionPoolTemplateFormSet(request.POST)
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.pool = pool
                instance.save()
            return redirect('exams:detail', pk=self.kwargs['exam_pk'])
        
        return self.render_to_response(self.get_context_data(formset=formset))
```

### Questions App View Updates

**apps/questions/views.py (updates):**
- Change all `Question` → `QuestionTemplate` in imports
- Update variable names for clarity (e.g., `question` → `template` where appropriate)
- Update context variable names or keep as `question` for backward compatibility
- Update success messages to say "Question template saved"

## Forms

### Exams App Forms

**apps/exams/forms.py:**
```python
from django import forms
from django.forms import modelformset_factory
from .models import Exam, QuestionPool, QuestionPoolTemplate

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Midterm Exam 2026'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional exam description'}),
        }

class QuestionPoolForm(forms.ModelForm):
    class Meta:
        model = QuestionPool
        fields = []  # Order is set automatically, no user-editable fields

QuestionPoolTemplateFormSet = modelformset_factory(
    QuestionPoolTemplate,
    fields=['template', 'number_of_versions'],
    extra=3,
    can_delete=True,
    widgets={
        'template': forms.Select(attrs={'class': 'form-select'}),
        'number_of_versions': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
    }
)
```

### Questions App Form Updates

**apps/questions/forms.py (updates):**
```python
# Change model reference
class QuestionForm(forms.ModelForm):  # Can keep form name or rename to QuestionTemplateForm
    class Meta:
        model = QuestionTemplate  # CHANGED from Question
        # ... rest unchanged
```

## Templates

### Exams App Templates

**apps/exams/templates/exams/exam_list.html:**
```django
{% extends 'common/base.html' %}
{% load static %}

{% block title %}Exams{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Exams</h1>
        <a href="{% url 'exams:create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Create Exam
        </a>
    </div>
    
    {% if exams %}
    <div class="table-responsive">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Pools</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for exam in exams %}
                <tr>
                    <td><a href="{% url 'exams:detail' exam.pk %}">{{ exam.title }}</a></td>
                    <td>{{ exam.date|date:"Y-m-d"|default:"—" }}</td>
                    <td>{{ exam.pools.count }} pool{{ exam.pools.count|pluralize }}</td>
                    <td>{{ exam.created_at|date:"Y-m-d" }}</td>
                    <td>
                        <a href="{% url 'exams:edit' exam.pk %}" class="btn btn-sm btn-outline-secondary">
                            <i class="fas fa-edit"></i>
                        </a>
                        <a href="{% url 'exams:delete' exam.pk %}" class="btn btn-sm btn-outline-danger">
                            <i class="fas fa-trash"></i>
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    {% include 'common/pagination.html' %}
    {% else %}
    <div class="alert alert-info">
        No exams yet. <a href="{% url 'exams:create' %}">Create your first exam</a>.
    </div>
    {% endif %}
</div>
{% endblock %}
```

**apps/exams/templates/exams/exam_detail.html:**
```django
{% extends 'common/base.html' %}
{% load static %}

{% block title %}{{ exam.title }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>{{ exam.title }}</h1>
        <div>
            <a href="{% url 'exams:edit' exam.pk %}" class="btn btn-outline-secondary">
                <i class="fas fa-edit"></i> Edit
            </a>
            <a href="{% url 'exams:delete' exam.pk %}" class="btn btn-outline-danger">
                <i class="fas fa-trash"></i> Delete
            </a>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-body">
            <p><strong>Date:</strong> {{ exam.date|date:"Y-m-d"|default:"Not set" }}</p>
            {% if exam.description %}
            <p><strong>Description:</strong> {{ exam.description }}</p>
            {% endif %}
        </div>
    </div>
    
    <h2>Question Pools</h2>
    
    {% if pools %}
    <div class="list-group mb-3">
        {% for pool in pools %}
        <div class="list-group-item">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h5>Pool {{ pool.order }}</h5>
                    <p class="mb-1">{{ pool.pool_templates.count }} template{{ pool.pool_templates.count|pluralize }}</p>
                    
                    {% if pool.pool_templates.exists %}
                    <ul class="list-unstyled ms-3">
                        {% for pt in pool.pool_templates.all %}
                        <li>
                            <i class="fas fa-check-circle text-success"></i>
                            {{ pt.template.title }}
                            <span class="badge bg-secondary">{{ pt.number_of_versions }} version{{ pt.number_of_versions|pluralize }}</span>
                            <a href="{% url 'exams:pool_template_delete' exam.pk pool.pk pt.pk %}" class="text-danger ms-2">
                                <i class="fas fa-times"></i>
                            </a>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                <div>
                    <a href="{% url 'exams:pool_template_add' exam.pk pool.pk %}" class="btn btn-sm btn-primary">
                        <i class="fas fa-plus"></i> Add Templates
                    </a>
                    <a href="{% url 'exams:pool_delete' exam.pk pool.pk %}" class="btn btn-sm btn-outline-danger">
                        <i class="fas fa-trash"></i>
                    </a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="alert alert-info">No question pools yet.</div>
    {% endif %}
    
    <a href="{% url 'exams:pool_create' exam.pk %}" class="btn btn-primary">
        <i class="fas fa-plus"></i> Add Pool
    </a>
</div>
{% endblock %}
```

**apps/exams/templates/exams/exam_form.html:**
```django
{% extends 'common/base.html' %}
{% load static %}

{% block title %}{% if form.instance.pk %}Edit{% else %}Create{% endif %} Exam{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>{% if form.instance.pk %}Edit{% else %}Create{% endif %} Exam</h1>
    
    <form method="post" class="mt-4">
        {% csrf_token %}
        
        <div class="mb-3">
            <label for="{{ form.title.id_for_label }}" class="form-label">Title *</label>
            {{ form.title }}
            {% if form.title.errors %}
            <div class="text-danger">{{ form.title.errors }}</div>
            {% endif %}
        </div>
        
        <div class="mb-3">
            <label for="{{ form.date.id_for_label }}" class="form-label">Date</label>
            {{ form.date }}
            {% if form.date.errors %}
            <div class="text-danger">{{ form.date.errors }}</div>
            {% endif %}
        </div>
        
        <div class="mb-3">
            <label for="{{ form.description.id_for_label }}" class="form-label">Description</label>
            {{ form.description }}
            {% if form.description.errors %}
            <div class="text-danger">{{ form.description.errors }}</div>
            {% endif %}
        </div>
        
        <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary">Save</button>
            <a href="{% if form.instance.pk %}{% url 'exams:detail' form.instance.pk %}{% else %}{% url 'exams:list' %}{% endif %}" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
```

**apps/exams/templates/exams/pool_template_add.html:**
```django
{% extends 'common/base.html' %}
{% load static %}

{% block title %}Add Templates to Pool{% endblock %}

{% block content %}
<div class="container mt-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="{% url 'exams:list' %}">Exams</a></li>
            <li class="breadcrumb-item"><a href="{% url 'exams:detail' exam.pk %}">{{ exam.title }}</a></li>
            <li class="breadcrumb-item active">Add Templates to Pool {{ pool.order }}</li>
        </ol>
    </nav>
    
    <h1>Add Templates to Pool {{ pool.order }}</h1>
    
    <form method="post" class="mt-4">
        {% csrf_token %}
        {{ formset.management_form }}
        
        <div class="mb-3">
            <label class="form-label">Select Question Templates</label>
            <p class="text-muted small">Choose templates and specify how many versions should be generated.</p>
        </div>
        
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>Template</th>
                        <th>Subject</th>
                        <th>Versions</th>
                        <th>Delete</th>
                    </tr>
                </thead>
                <tbody>
                    {% for form in formset %}
                    <tr>
                        <td>{{ form.template }}</td>
                        <td>
                            <span class="badge bg-info">
                                {% if form.template.value %}
                                    {{ available_templates|dictsort:"id"|get_item:form.template.value|get_attr:"subject.name" }}
                                {% endif %}
                            </span>
                        </td>
                        <td>{{ form.number_of_versions }}</td>
                        <td>{{ form.DELETE }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary">Add Templates</button>
            <a href="{% url 'exams:detail' exam.pk %}" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
```

### Questions App Template Updates

**Update all templates:**
- Change page titles from "Questions" to "Question Templates"
- Update breadcrumbs and navigation labels
- Update form labels and help text to reference "template"
- Keep URL paths unchanged (still `/questions/`)

Example updates:
```django
<!-- Before -->
<h1>Create Question</h1>

<!-- After -->
<h1>Create Question Template</h1>
```

## Navigation Updates

**apps/common/templates/common/base.html (update nav):**
```django
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
        <a class="navbar-brand" href="/">Qoodle</a>
        <div class="collapse navbar-collapse">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'subjects:list' %}">Manage Subjects</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'questions:list' %}">Manage Question Templates</a> <!-- UPDATED -->
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'exams:list' %}">Manage Exams</a> <!-- NEW -->
                </li>
            </ul>
        </div>
    </div>
</nav>
```

## Admin Integration

**apps/exams/admin.py:**
```python
from django.contrib import admin
from .models import Exam, QuestionPool, QuestionPoolTemplate

class QuestionPoolInline(admin.TabularInline):
    model = QuestionPool
    extra = 1
    fields = ['order']

class QuestionPoolTemplateInline(admin.TabularInline):
    model = QuestionPoolTemplate
    extra = 1
    fields = ['template', 'number_of_versions']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'pool_count', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['date', 'created_at']
    inlines = [QuestionPoolInline]
    
    def pool_count(self, obj):
        return obj.pools.count()
    pool_count.short_description = 'Pools'

@admin.register(QuestionPool)
class QuestionPoolAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'exam', 'order', 'template_count']
    list_filter = ['exam']
    inlines = [QuestionPoolTemplateInline]
    
    def template_count(self, obj):
        return obj.pool_templates.count()
    template_count.short_description = 'Templates'

@admin.register(QuestionPoolTemplate)
class QuestionPoolTemplateAdmin(admin.ModelAdmin):
    list_display = ['pool', 'template', 'number_of_versions']
    list_filter = ['pool__exam']
```

**apps/questions/admin.py (update):**
```python
from .models import QuestionTemplate, Choice  # UPDATED import

@admin.register(QuestionTemplate)  # UPDATED
class QuestionTemplateAdmin(admin.ModelAdmin):  # RENAMED
    # ... rest unchanged
```

## Testing Strategy

### Test Coverage Requirements

**Target:** 80% coverage minimum

**Test files:**
- `apps/exams/tests.py` - All exam/pool tests
- `apps/questions/tests.py` - Update existing tests for rename

### Test Categories

**Model Tests:**
```python
class ExamModelTests(TestCase):
    def test_create_exam_with_required_title(self):
        """Exam can be created with just title"""
    
    def test_create_exam_with_all_fields(self):
        """Exam can be created with all optional fields"""
    
    def test_exam_str_returns_title(self):
        """String representation returns title"""
    
    def test_delete_exam_cascades_to_pools(self):
        """Deleting exam deletes all pools"""
    
    def test_delete_exam_does_not_delete_templates(self):
        """Deleting exam preserves question templates"""

class QuestionPoolModelTests(TestCase):
    def test_pool_unique_order_per_exam(self):
        """Cannot have duplicate order in same exam"""
    
    def test_pool_allows_same_order_different_exams(self):
        """Different exams can have pools with same order"""
    
    def test_delete_pool_unlinks_templates(self):
        """Deleting pool removes template associations"""

class QuestionPoolTemplateModelTests(TestCase):
    def test_unique_template_per_pool(self):
        """Cannot add same template twice to one pool"""
    
    def test_number_of_versions_minimum_one(self):
        """Validation fails if versions < 1"""
    
    def test_same_template_different_pools_allowed(self):
        """Same template can be in different pools"""
```

**View Tests:**
```python
class ExamViewTests(TestCase):
    def test_exam_list_displays_all_exams(self):
        """List view shows all exams"""
    
    def test_exam_create_requires_title(self):
        """Form validation fails without title"""
    
    def test_exam_delete_confirmation(self):
        """Delete view shows confirmation page"""

class PoolManagementViewTests(TestCase):
    def test_add_pool_sets_correct_order(self):
        """New pool gets max_order + 1"""
    
    def test_pool_template_add_excludes_existing(self):
        """Template selection excludes already-added templates"""
```

**Integration Tests:**
```python
class ExamWorkflowIntegrationTests(TestCase):
    def test_full_exam_creation_workflow(self):
        """
        End-to-end:
        1. Create exam
        2. Add 3 pools
        3. Add templates to each pool
        4. Verify structure
        """
    
    def test_duplicate_prevention_workflow(self):
        """
        Cannot add same template to same pool twice,
        but can add to different pools
        """
```

**Rename Migration Tests:**
```python
class QuestionTemplateRenameTests(TestCase):
    def test_question_renamed_to_questiontemplate(self):
        """Model name is QuestionTemplate not Question"""
    
    def test_choice_fk_renamed_to_template(self):
        """Choice has 'template' FK not 'question'"""
    
    def test_existing_data_preserved(self):
        """All question data survives rename"""
```

## Risks / Trade-offs

### Risk 1: Rename Breaks External Integrations

**Risk:** If any external systems reference the `Question` model by name, rename will break them.

**Mitigation:**
- Project is early-stage (no known external integrations)
- Django migrations handle database rename automatically
- Can add backward-compatible imports if needed: `Question = QuestionTemplate`

**Trade-off:** Accept risk for better code clarity.

### Risk 2: Large Formsets Performance

**Risk:** If a pool has 100+ available templates, formset rendering may be slow.

**Mitigation:**
- Start with simple formset (defer optimization)
- Add pagination or AJAX search if needed later
- Most exams will have <50 templates realistically

**Trade-off:** Choose simplicity now, optimize if proven necessary.

### Risk 3: Pool Ordering Conflicts

**Risk:** Manual order management could lead to conflicts (two pools with same order).

**Mitigation:**
- Database constraint `unique_together = [('exam', 'order')]`
- View logic auto-assigns order (no manual input)
- Reorder view handles swapping carefully

**Trade-off:** Simple integer ordering vs. complex library (django-ordered-model).

### Risk 4: Test Coverage Below 80% During Rename

**Risk:** Comprehensive rename testing may be difficult, coverage could drop temporarily.

**Mitigation:**
- Run full test suite before rename
- Update tests incrementally during rename
- Accept temporary coverage dip, recover quickly

**Trade-off:** Practical rename workflow vs. strict coverage enforcement.

### Risk 5: UI Complexity for Template Selection

**Risk:** Selecting templates from long lists with subject filtering may confuse users.

**Mitigation:**
- Start with simple select dropdowns in formset
- Add subject filter dropdown if needed
- Future: AJAX search/autocomplete

**Trade-off:** Ship basic UI fast, iterate based on user feedback.
