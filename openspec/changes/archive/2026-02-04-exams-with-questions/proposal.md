# Proposal: Exam Management with Question Pools

## Why

### Problem Statement

Currently, Qoodle allows teachers to create individual questions with variables for randomization, but there's no way to:

1. **Organize questions into structured exams** - Questions exist independently without grouping into assessments
2. **Create exam variants** - No systematic way to generate multiple exam versions to prevent cheating
3. **Control question distribution** - Cannot specify how many versions of each question should be generated
4. **Prevent question duplication** - Risk of same question appearing multiple times in an exam

### User Need

Teachers need to create exams where:
- Each exam has an ordered sequence of question "slots" (pools)
- Each slot can contain multiple alternative questions of similar difficulty
- Each question can be generated with different variable values (using existing variable system)
- Moodle will randomly select one question from each pool when students take the exam
- The system prevents the same question template from appearing twice in the same exam

### Context

This builds directly on the existing **variable system** (questions with `{{variables}}` and seeded generation). The exam system will leverage these question variants to create diverse exam versions without manual duplication.

## What Changes

### Core Changes

**1. Rename Question → QuestionTemplate**

Rename the existing `Question` model to `QuestionTemplate` throughout the entire codebase to better reflect its purpose as a template that generates multiple question instances through variable substitution.

**Scope of rename:**
- Model: `apps/questions/models.py` - `Question` → `QuestionTemplate`
- Database table: `questions_question` → `questions_questiontemplate`
- All views, forms, templates, URLs, tests
- All references in `Choice` model (foreign key)
- Navigation items, page titles, breadcrumbs

**2. New Exam Management System**

Add three new models to support exam creation:

- **Exam** - Top-level container for an assessment
- **QuestionPool** - Ordered slot within an exam containing alternative questions
- **QuestionPoolTemplate** - Through table linking pools to question templates with version count

### Model Structure

```
Exam
  ├─ title (CharField, required)
  ├─ date (DateField, optional)
  ├─ description (TextField, optional)
  └─ QuestionPool (many, ordered)
      ├─ order (PositiveIntegerField)
      └─ QuestionTemplate (many-to-many through QuestionPoolTemplate)
          └─ number_of_versions (PositiveIntegerField, default=1)
```

### UI Changes

1. **Navigation Update:**
   - Remove "Manage Languages" from main navigation (not implemented)
   - Add "Manage Exams" menu item

2. **New Pages:**
   - Exam list view (browse all exams)
   - Exam create/edit form
   - QuestionPool management within exam (add/remove/reorder)
   - QuestionTemplate selection interface (filter by subject, checkbox selection)

3. **Workflow:**
   - Create exam → Add question pools → Select question templates → Set version counts

## Capabilities

### New Capabilities

1. **exam-management** (NEW)
   - Create, read, update, delete exams
   - Manage exam metadata (title, date, description)

2. **question-pool-management** (NEW)
   - Add ordered question pools to exams
   - Reorder pools within an exam
   - Remove pools from exams

3. **question-pool-composition** (NEW)
   - Add multiple question templates to a pool
   - Set number of versions per template
   - Prevent duplicate templates within the same exam
   - Filter available templates by subject

### Modified Capabilities

1. **multilingual-questions** (MODIFIED)
   - Rename from "questions" to "question-templates"
   - All existing functionality preserved
   - Model name change only affects internal references

2. **navigation** (MODIFIED)
   - Remove "Manage Languages" placeholder
   - Add "Manage Exams" menu item

## Impact

### Database Changes

**Migration 1: Rename Question → QuestionTemplate**
```python
operations = [
    migrations.RenameModel(
        old_name='Question',
        new_name='QuestionTemplate',
    ),
]
```

**Migration 2: Add Exam models**
```python
operations = [
    migrations.CreateModel(
        name='Exam',
        fields=[
            ('id', UUIDField(primary_key=True, default=uuid.uuid4)),
            ('title', CharField(max_length=255)),
            ('date', DateField(null=True, blank=True)),
            ('description', TextField(blank=True)),
            ('created_at', DateTimeField(auto_now_add=True)),
            ('updated_at', DateTimeField(auto_now=True)),
        ],
    ),
    migrations.CreateModel(
        name='QuestionPool',
        fields=[
            ('id', UUIDField(primary_key=True, default=uuid.uuid4)),
            ('exam', ForeignKey(related_name='pools')),
            ('order', PositiveIntegerField()),
            ('created_at', DateTimeField(auto_now_add=True)),
            ('updated_at', DateTimeField(auto_now=True)),
        ],
    ),
    migrations.CreateModel(
        name='QuestionPoolTemplate',
        fields=[
            ('id', UUIDField(primary_key=True, default=uuid.uuid4)),
            ('pool', ForeignKey(related_name='pool_templates')),
            ('template', ForeignKey(related_name='pool_memberships')),
            ('number_of_versions', PositiveIntegerField(default=1)),
            ('created_at', DateTimeField(auto_now_add=True)),
        ],
    ),
]
```

### Code Impact

**High-impact areas:**
- `apps/questions/` - Entire app affected by rename
- All existing templates referencing "question"
- All URLs (`/questions/` paths remain, internal names change)
- All tests using Question model
- Admin interface

**Low-impact areas:**
- Subject app (only foreign key reference name changes)
- Common templates (base.html navigation)

### URL Structure

**Existing (renamed):**
- `/questions/` → Lists question templates
- `/questions/create/` → Create question template
- `/questions/<uuid>/` → View question template
- `/questions/<uuid>/edit/` → Edit question template
- `/questions/<uuid>/preview/` → Preview question template

**New:**
- `/exams/` → List exams
- `/exams/create/` → Create exam
- `/exams/<uuid>/` → View exam details
- `/exams/<uuid>/edit/` → Edit exam
- `/exams/<uuid>/pools/` → Manage question pools
- `/exams/<uuid>/pools/<uuid>/templates/` → Manage templates in pool

### User Experience Changes

**For teachers:**
- ✅ Familiar question creation remains identical
- ✅ New "Exams" section in navigation
- ✅ Clear distinction between question templates and exams
- ⚠️ Must learn new exam creation workflow

**Backward compatibility:**
- ✅ All existing question templates preserved
- ✅ All existing question data intact
- ✅ No changes to question functionality
- ✅ URL paths remain the same

## Implementation Phases

### Phase 1: Question Rename (Foundation)
1. Create migration for model rename
2. Update all model references
3. Update views, forms, serializers
4. Update templates and static files
5. Update URLs and routing
6. Update tests
7. Update admin interface
8. Verify all existing tests pass

### Phase 2: Exam Models (Core)
1. Create Exam, QuestionPool, QuestionPoolTemplate models
2. Create migrations
3. Add model validators (unique templates per exam)
4. Add ordering logic for pools
5. Write model tests

### Phase 3: Exam CRUD (Basic UI)
1. Create exam list view
2. Create exam create/edit forms
3. Create exam detail view
4. Add navigation menu item
5. Create templates

### Phase 4: Question Pool Management (Advanced UI)
1. Pool add/remove/reorder interface
2. Template selection UI with subject filter
3. Version count input per template
4. Duplicate prevention logic
5. Bulk pool creation

## Risks & Mitigation

### High Risk: Model Rename

**Risk:** Renaming `Question` affects hundreds of lines of code and could break existing functionality.

**Mitigation:**
- Create comprehensive test coverage BEFORE rename
- Use Django's RenameModel migration (handles DB automatically)
- Systematic find-replace with verification at each step
- Run full test suite after each component is updated
- Keep one commit per logical grouping (models, then views, then templates)

### Medium Risk: Question Duplication

**Risk:** Same question template appearing multiple times in one exam.

**Mitigation:**
- Model-level constraint: `unique_together = [('pool__exam', 'template')]` validation
- Form-level validation before save
- UI-level: Disable already-selected templates in selection interface
- Clear error messages when duplicate detected

### Low Risk: Complex UI

**Risk:** Managing pools and templates could be confusing with nested relationships.

**Mitigation:**
- Progressive disclosure: Start simple (create exam, add one pool, add one template)
- Inline pool management on exam edit page (similar to choice management in questions)
- JavaScript drag-and-drop for pool reordering
- Clear visual hierarchy (exam → pools → templates)

## Dependencies

### Existing Dependencies (No new packages needed)
- Django 6.0.1 - Model migrations, admin
- Bootstrap 5.3.8 - UI for forms and lists
- FontAwesome 7.1.0 - Icons for pools and exams
- pytest-django - Testing

### New App Structure
```
apps/exams/
├── models.py          # Exam, QuestionPool, QuestionPoolTemplate
├── views.py           # CRUD views for exams
├── forms.py           # ExamForm, pool management
├── urls.py            # /exams/ routes
├── admin.py           # Admin interface
├── tests.py           # >80% coverage
├── templates/exams/
│   ├── exam_list.html
│   ├── exam_form.html
│   ├── exam_detail.html
│   └── pool_management.html
└── static/exams/
    └── js/
        └── pool_manager.js    # Drag-drop, template selection
```

## Testing Strategy

### Unit Tests (Model Layer)
- QuestionTemplate rename doesn't break existing tests
- Exam creation with validation
- QuestionPool ordering
- Duplicate template prevention
- Version count validation (must be ≥ 1)

### Integration Tests (View Layer)
- Create exam through form
- Add pools to exam
- Select templates for pool
- Prevent duplicate template selection
- Reorder pools

### UI Tests (Manual)
- Navigate from "Manage Exams"
- Create exam with 3 pools
- Add 2-3 templates per pool
- Set different version counts
- Verify duplicate prevention works

## Verification Plan

### Pre-deployment Checklist

1. **Rename Verification:**
   ```bash
   poetry run python manage.py makemigrations
   poetry run python manage.py migrate
   poetry run pytest apps/questions/tests.py  # All existing tests pass
   ```

2. **New Models Verification:**
   ```bash
   poetry run python manage.py shell
   >>> from apps.exams.models import Exam, QuestionPool
   >>> exam = Exam.objects.create(title="Test Exam")
   >>> pool = QuestionPool.objects.create(exam=exam, order=1)
   >>> print(pool)  # Verify __str__ method
   ```

3. **Duplicate Prevention Test:**
   ```python
   # In Django shell
   from apps.exams.models import Exam, QuestionPool, QuestionPoolTemplate
   from apps.questions.models import QuestionTemplate
   
   exam = Exam.objects.create(title="Test")
   pool1 = QuestionPool.objects.create(exam=exam, order=1)
   pool2 = QuestionPool.objects.create(exam=exam, order=2)
   template = QuestionTemplate.objects.first()
   
   QuestionPoolTemplate.objects.create(pool=pool1, template=template, number_of_versions=5)
   QuestionPoolTemplate.objects.create(pool=pool2, template=template, number_of_versions=3)
   # Should raise ValidationError
   ```

4. **Coverage Check:**
   ```bash
   poetry run pytest --cov=apps/exams --cov-report=term-missing
   # Target: >80% coverage
   ```

## Out of Scope (Future Work)

The following are explicitly NOT included in this change:

- ❌ Moodle XML export functionality
- ❌ Variable value generation for exam instances
- ❌ Student-facing exam interface
- ❌ Grading or scoring system
- ❌ Exam scheduling or access control
- ❌ Question template statistics (usage tracking)
- ❌ Exam templates or duplication
- ❌ Import from external formats

These will be addressed in future changes after the core exam structure is validated.

## Success Criteria

This change is successful when:

1. ✅ All `Question` references renamed to `QuestionTemplate` with zero regressions
2. ✅ Teachers can create exams with title, date, description
3. ✅ Teachers can add multiple question pools to an exam with ordering
4. ✅ Teachers can add multiple question templates to each pool
5. ✅ Teachers can set version count per template (≥1)
6. ✅ System prevents same template from appearing twice in one exam
7. ✅ All existing question functionality works unchanged
8. ✅ Test coverage remains >80%
9. ✅ "Manage Exams" appears in navigation
10. ✅ Database migrations run cleanly on fresh and existing databases

## Timeline Estimate

- **Phase 1 (Rename):** 2-3 days
- **Phase 2 (Models):** 1-2 days  
- **Phase 3 (Basic CRUD):** 2-3 days
- **Phase 4 (Pool Management):** 3-4 days
- **Testing & Polish:** 2 days

**Total:** ~10-14 days for complete implementation and testing
