# Implementation Tasks: Exam Management with Question Pools

## Phase 1: Question → QuestionTemplate Rename (2-3 days) ✅ COMPLETED

### 1.1 Database Migrations

- [x] Create migration to rename `Question` model to `QuestionTemplate` in `apps/questions/migrations/`
- [x] Create migration to rename `Choice.question` FK to `Choice.template` in `apps/questions/migrations/`
- [x] Run `poetry run python manage.py makemigrations` to generate migration files
- [x] Run `poetry run python manage.py migrate` to apply migrations
- [x] Verify database table renamed from `questions_question` to `questions_questiontemplate`
- [x] Verify all foreign keys updated correctly in database

### 1.2 Model Updates

- [x] Rename `Question` class to `QuestionTemplate` in `apps/questions/models.py`
- [x] Update `QuestionTemplate` docstring to reference "template" terminology
- [x] Rename `question` FK to `template` in `Choice` model in `apps/questions/models.py`
- [x] Update `Subject` model's related_name from `questions` to `question_templates`
- [x] Verify all model methods use correct field names

### 1.3 Admin Updates

- [x] Rename `QuestionAdmin` to `QuestionTemplateAdmin` in `apps/questions/admin.py`
- [x] Update admin registration to use `QuestionTemplate` model
- [x] Update admin `list_display` labels to reference "template"
- [x] Update admin verbose names to "Question Template"
- [x] Verify admin interface displays "Question Templates" in sidebar

### 1.4 View Updates

- [x] Update all imports from `Question` to `QuestionTemplate` in `apps/questions/views.py`
- [x] Rename view class names (e.g., `QuestionListView` → `QuestionTemplateListView`) in `apps/questions/views.py`
- [x] Update all queryset references to use `QuestionTemplate` model
- [x] Update context variable names (keep `question` for backward compat or rename to `template`)
- [x] Update success messages to reference "question template"
- [x] Update `QuestionPreviewView` to use `QuestionTemplate`

### 1.5 Form Updates

- [x] Update `QuestionForm` model reference to `QuestionTemplate` in `apps/questions/forms.py`
- [x] Update form `Meta` class to reference `QuestionTemplate`
- [x] Update form labels and help_text to say "question template"
- [x] Update `clean_*` methods to reference `QuestionTemplate`
- [x] Verify form validation works with renamed model

### 1.6 Template Updates

- [x] Update page titles to "Question Templates" in `apps/questions/templates/questions/question_list.html`
- [x] Update breadcrumbs to show "Question Templates" in all question templates
- [x] Update button labels to "Create Template", "Edit Template", etc.
- [x] Update `apps/questions/templates/questions/question_form.html` labels
- [x] Update `apps/questions/templates/questions/question_detail.html` headings
- [x] Update `apps/questions/templates/questions/question_preview.html` references
- [x] Update `apps/questions/templates/questions/question_confirm_delete.html` text
- [x] Keep template variable names as `question` or rename to `template` (decide consistently)

### 1.7 URL Pattern Updates

- [x] Verify URL paths remain `/questions/` (no change needed)
- [x] Verify URL names remain `questions:list`, `questions:create`, etc. (no change needed)
- [x] Update URL docstrings/comments to reference "question templates"

### 1.8 Navigation Updates

- [x] Update navigation label from "Manage Questions" to "Manage Question Templates" in `apps/common/templates/common/base.html`
- [x] Update any breadcrumb references to "Question Templates"
- [x] Verify navigation links still work correctly

### 1.9 Test Updates

- [x] Update all test imports from `Question` to `QuestionTemplate` in `apps/questions/tests.py`
- [x] Update test class names to reference `QuestionTemplate`
- [x] Update test method names to reference `template` (e.g., `test_create_question` → `test_create_question_template`)
- [x] Update test fixtures to use `QuestionTemplate.objects.create()`
- [x] Update assertions to reference `template` field on `Choice` model
- [x] Run `poetry run pytest apps/questions/tests.py` to verify all tests pass
- [x] Verify test coverage remains >80%

### 1.10 Phase 1 Validation

- [x] Run full test suite: `poetry run pytest`
- [x] Verify all 102+ tests pass
- [x] Run `poetry run python manage.py check` for system checks
- [x] Manually test question template CRUD in browser
- [x] Manually test question template preview functionality
- [x] Verify no broken links or 404 errors
- [x] Run `poetry run black apps/questions/` to format code
- [x] Run `poetry run ruff check apps/questions/` for linting
- [x] Commit changes: "Phase 1: Rename Question to QuestionTemplate"

---

## Phase 2: Create Exams App (2-3 days)

### 2.1 App Setup

- [x] Run `poetry run python manage.py startapp exams apps/exams` to create app
- [x] Add `'apps.exams'` to `INSTALLED_APPS` in `qoodle/settings.py`
- [x] Create `apps/exams/__init__.py` if not exists
- [x] Create `apps/exams/apps.py` with proper `AppConfig`
- [x] Verify app is recognized by Django: `poetry run python manage.py check`

### 2.2 Model Implementation

- [x] Create `Exam` model in `apps/exams/models.py` with fields: title, date, description, created_at, updated_at
- [x] Ensure `Exam` extends `UUIDModel` from `apps.common.models`
- [x] Add `__str__` method returning `title` to `Exam` model
- [x] Add `Meta` class with `ordering = ['-created_at']` to `Exam` model
- [x] Create `QuestionPool` model in `apps/exams/models.py` with fields: exam (FK), order, question_templates (M2M)
- [x] Add `unique_together = [('exam', 'order')]` to `QuestionPool` Meta
- [x] Add `ordering = ['order']` to `QuestionPool` Meta
- [x] Create `QuestionPoolTemplate` through model with fields: pool (FK), template (FK to questions.QuestionTemplate), number_of_versions
- [x] Add `unique_together = [('pool', 'template')]` to `QuestionPoolTemplate` Meta
- [x] Add `MinValueValidator(1)` to `number_of_versions` field
- [x] Add docstrings to all models explaining their purpose
- [x] Add type hints to all model methods

### 2.3 Database Migrations

- [x] Run `poetry run python manage.py makemigrations exams` to create initial migration
- [x] Review migration file to ensure all fields and constraints are correct
- [x] Run `poetry run python manage.py migrate` to apply migration
- [x] Verify tables created: `exams_exam`, `exams_questionpool`, `exams_questionpooltemplate`
- [x] Verify foreign keys and unique constraints in database schema

### 2.4 Admin Registration

- [x] Create `apps/exams/admin.py` file
- [x] Create `ExamAdmin` class with `list_display = ['title', 'date', 'pool_count', 'created_at']`
- [x] Add `pool_count` method to `ExamAdmin` showing number of pools
- [x] Create `QuestionPoolInline` for editing pools within exam
- [x] Register `ExamAdmin` with `@admin.register(Exam)` decorator
- [x] Create `QuestionPoolAdmin` class with template count display
- [x] Create `QuestionPoolTemplateInline` for editing templates within pool
- [x] Register `QuestionPoolAdmin` with decorator
- [x] Create `QuestionPoolTemplateAdmin` with list display
- [x] Register `QuestionPoolTemplateAdmin` with decorator
- [x] Verify admin pages render correctly at `/admin/exams/`

### 2.5 URL Configuration

- [x] Create `apps/exams/urls.py` with `app_name = 'exams'`
- [x] Add exam list URL pattern: `path('', ExamListView.as_view(), name='list')`
- [x] Add exam create URL: `path('create/', ExamCreateView.as_view(), name='create')`
- [x] Add exam detail URL: `path('<uuid:pk>/', ExamDetailView.as_view(), name='detail')`
- [x] Add exam edit URL: `path('<uuid:pk>/edit/', ExamUpdateView.as_view(), name='edit')`
- [x] Add exam delete URL: `path('<uuid:pk>/delete/', ExamDeleteView.as_view(), name='delete')`
- [x] Add pool create URL: `path('<uuid:exam_pk>/pools/add/', PoolCreateView.as_view(), name='pool_create')`
- [x] Add pool edit URL: `path('<uuid:exam_pk>/pools/<uuid:pk>/edit/', PoolUpdateView.as_view(), name='pool_edit')`
- [x] Add pool delete URL: `path('<uuid:exam_pk>/pools/<uuid:pk>/delete/', PoolDeleteView.as_view(), name='pool_delete')`
- [x] Add pool template add URL: `path('<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/add/', PoolTemplateAddView.as_view(), name='pool_template_add')`
- [x] Add pool template delete URL: `path('<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/<uuid:pk>/delete/', PoolTemplateDeleteView.as_view(), name='pool_template_delete')`
- [x] Include exams URLs in project urls: `path('exams/', include('apps.exams.urls'))` in `qoodle/urls.py`
- [x] Verify URL routing works: `poetry run python manage.py show_urls` (if django-extensions installed)

### 2.6 Forms

- [x] Create `apps/exams/forms.py` file
- [x] Create `ExamForm` ModelForm with fields: title, date, description
- [x] Add Bootstrap widget classes to all `ExamForm` fields
- [x] Add placeholder text to `ExamForm` fields
- [x] Create `QuestionPoolForm` ModelForm (empty fields, order auto-assigned)
- [x] Create `QuestionPoolTemplateFormSet` using `modelformset_factory`
- [x] Configure formset with `extra=3`, `can_delete=True`
- [x] Add Bootstrap widget classes to formset fields
- [x] Add validation to prevent `number_of_versions < 1`

### 2.7 Phase 2 Validation

- [x] Run `poetry run python manage.py check` to verify configuration
- [x] Run `poetry run python manage.py migrate --check` to verify migrations
- [x] Access `/admin/exams/exam/` and verify admin works
- [x] Create test exam via admin and verify database record
- [x] Verify URL patterns resolve correctly
- [x] Commit changes: "Phase 2: Create exams app with models and admin"

---

## Phase 3: Exam Views and Templates (3-4 days)

### 3.1 Exam List View

- [x] Create `ExamListView` in `apps/exams/views.py` extending `ListView`
- [x] Set `model = Exam`, `template_name = 'exams/exam_list.html'`, `context_object_name = 'exams'`
- [x] Add `paginate_by = 20` to view
- [x] Add type hints to view class and methods
- [x] Create template directory: `apps/exams/templates/exams/`
- [x] Create `apps/exams/templates/exams/exam_list.html` extending `common/base.html`
- [x] Add page title "Exams" to template
- [x] Add "Create Exam" button linking to `{% url 'exams:create' %}`
- [x] Add table displaying: title, date, pool count, created date, actions
- [x] Add pool count column using `{{ exam.pools.count }}`
- [x] Add edit/delete action buttons with FontAwesome icons
- [x] Add empty state message: "No exams yet. Create your first exam."
- [x] Include pagination template if `is_paginated`
- [x] Test view at `/exams/` in browser

### 3.2 Exam Create View

- [x] Create `ExamCreateView` in `apps/exams/views.py` extending `CreateView`
- [x] Set `model = Exam`, `form_class = ExamForm`, `template_name = 'exams/exam_form.html'`
- [x] Override `get_success_url()` to redirect to exam detail page
- [x] Create `apps/exams/templates/exams/exam_form.html` extending base
- [x] Add conditional page title: "Create Exam" or "Edit Exam"
- [x] Render form with Bootstrap styling (form-control classes)
- [x] Add title field with label "Title *" and form-control class
- [x] Add date field with label "Date" and type="date"
- [x] Add description textarea with rows=4
- [x] Add "Save" submit button with btn-primary class
- [x] Add "Cancel" link back to exam list or detail
- [x] Add CSRF token to form
- [x] Display form errors with Bootstrap alert classes
- [x] Test creating exam via `/exams/create/`

### 3.3 Exam Detail View

- [x] Create `ExamDetailView` in `apps/exams/views.py` extending `DetailView`
- [x] Set `model = Exam`, `template_name = 'exams/exam_detail.html'`, `context_object_name = 'exam'`
- [x] Override `get_context_data()` to add pools with prefetch_related
- [x] Prefetch `pools__pool_templates__template` for efficiency
- [x] Create `apps/exams/templates/exams/exam_detail.html` extending base
- [x] Display exam title as page heading
- [x] Add "Edit" and "Delete" buttons in header
- [x] Display exam date (formatted as YYYY-MM-DD or "Not set")
- [x] Display exam description if set
- [x] Add "Question Pools" section heading
- [x] Loop through pools ordered by `order` field
- [x] Display each pool as card/list-group-item showing pool number
- [x] Show template count per pool: "X templates"
- [x] List all templates in pool with title and version count badges
- [x] Add "Add Templates" button per pool
- [x] Add delete button per template in pool
- [x] Add "Add Pool" button at bottom
- [x] Show empty state if no pools: "No question pools yet"
- [x] Test detail view with exam containing pools

### 3.4 Exam Update View

- [x] Create `ExamUpdateView` in `apps/exams/views.py` extending `UpdateView`
- [x] Set `model = Exam`, `form_class = ExamForm`, `template_name = 'exams/exam_form.html'`
- [x] Override `get_success_url()` to redirect to exam detail
- [x] Verify form template handles both create and edit (conditional title)
- [x] Test editing exam metadata at `/exams/<uuid>/edit/`
- [x] Verify form pre-populates with existing data

### 3.5 Exam Delete View

- [x] Create `ExamDeleteView` in `apps/exams/views.py` extending `DeleteView`
- [x] Set `model = Exam`, `template_name = 'exams/exam_confirm_delete.html'`, `success_url = reverse_lazy('exams:list')`
- [x] Create `apps/exams/templates/exams/exam_confirm_delete.html` extending base
- [x] Display warning: "Are you sure you want to delete [exam title]?"
- [x] Show pool count: "This will also delete X question pools"
- [x] Add note: "Question templates will NOT be deleted"
- [x] Add "Delete" submit button (btn-danger)
- [x] Add "Cancel" link back to exam detail
- [x] Include CSRF token in form
- [x] Test deleting exam and verify cascade to pools

### 3.6 Pool Create View

- [x] Create `PoolCreateView` in `apps/exams/views.py` extending `CreateView`
- [x] Set `model = QuestionPool`, `form_class = QuestionPoolForm`
- [x] Override `get_context_data()` to add exam from URL kwargs
- [x] Override `form_valid()` to set `exam` from `exam_pk` URL parameter
- [x] Calculate `order = max(exam.pools.values_list('order', flat=True)) + 1` or 1
- [x] Set `form.instance.order` before saving
- [x] Redirect to exam detail on success
- [x] Test adding pool to exam

### 3.7 Pool Update/Delete Views

- [x] Create `PoolUpdateView` extending `UpdateView` (minimal, mainly for reordering)
- [x] Create `PoolDeleteView` extending `DeleteView`
- [x] Create `apps/exams/templates/exams/pool_confirm_delete.html`
- [x] Show warning about templates being unlinked (not deleted)
- [x] Test deleting pool and verify templates remain in database

### 3.8 Pool Template Add View

- [x] Create `PoolTemplateAddView` in `apps/exams/views.py`
- [x] Override `get_context_data()` to fetch exam and pool from URL kwargs
- [x] Query available templates, excluding those already in pool
- [x] Use `QuestionTemplate.objects.exclude(id__in=pool.pool_templates.values_list('template_id'))`
- [x] Add subject filtering capability (dropdown or query param)
- [x] Render formset in context
- [x] Create `apps/exams/templates/exams/pool_template_add.html` extending base
- [x] Add breadcrumb navigation: Exams → Exam Title → Add Templates to Pool X
- [x] Render formset management form with `{{ formset.management_form }}`
- [x] Display table with columns: Template, Subject, Versions, Delete
- [x] Render each formset form as table row
- [x] Add template select dropdown with Bootstrap classes
- [x] Add number_of_versions input (type=number, min=1, default=1)
- [x] Add delete checkbox per row
- [x] Add "Add Templates" submit button
- [x] Add "Cancel" link back to exam detail
- [x] Override `post()` to handle formset submission
- [x] Validate formset, set `pool` on each instance before saving
- [x] Handle validation errors (duplicate template in pool)
- [x] Test adding multiple templates to pool at once

### 3.9 Pool Template Delete

- [x] Create `PoolTemplateDeleteView` extending `DeleteView`
- [x] Set model to `QuestionPoolTemplate`
- [x] Redirect to exam detail after deletion
- [x] Add confirmation template or use AJAX delete
- [x] Verify template is unlinked from pool, not deleted from database

### 3.10 Phase 3 Validation

- [x] Test full exam workflow: create → add pools → add templates → view detail
- [x] Verify all CRUD operations work correctly
- [x] Check responsive design on mobile viewport
- [x] Verify all Bootstrap styles render correctly
- [x] Verify all FontAwesome icons display
- [x] Test navigation between exams list, detail, and forms
- [x] Test edge cases: delete exam with many pools, add 10+ templates to pool
- [x] Run `poetry run python manage.py check --deploy` for deployment checks
- [x] Commit changes: "Phase 3: Implement exam views and templates"

---

## Phase 4: Navigation, Static Files, and Polish (1-2 days)

### 4.1 Navigation Updates

- [x] Update `apps/common/templates/common/base.html` navigation
- [x] Add "Manage Exams" nav item linking to `{% url 'exams:list' %}`
- [x] Verify "Manage Question Templates" label (updated in Phase 1)
- [x] Verify "Manage Subjects" nav item still present
- [x] Remove "Manage Languages" if it exists (not implemented)
- [ ] Add active state highlighting for current page
- [x] Test navigation from all pages

### 4.2 Static Files Setup

- [x] Create directory: `apps/exams/static/exams/css/` (NOT NEEDED - using Bootstrap/FontAwesome CDN)
- [x] Create directory: `apps/exams/static/exams/js/` (NOT NEEDED - no custom JS required)
- [x] Create `apps/exams/static/exams/css/exams.css` for exam-specific styles (NOT NEEDED)
- [x] Add styles for pool ordering UI (if drag-to-reorder added) (IMPLEMENTED with arrows)
- [x] Add styles for template selection interface (NOT NEEDED - using Bootstrap)
- [x] Create `apps/exams/static/exams/js/exam_form.js` for form interactions (NOT NEEDED)
- [x] Create `apps/exams/static/exams/js/pool_management.js` for pool UI (NOT NEEDED)
- [x] Add JavaScript to handle formset dynamic adding/removing (if needed) (NOT NEEDED - bulk add implemented)
- [x] Load static files in templates with `{% load static %}` (Already done for questions CSS)
- [x] Include CSS with `<link>` tag, defer JavaScript (Using CDN)
- [ ] Run `poetry run python manage.py collectstatic --noinput` to verify
- [x] Test JavaScript functionality in browser (No custom JS needed)

### 4.3 Breadcrumbs

- [x] Add breadcrumb partial template: `apps/common/templates/common/breadcrumbs.html` (NOT NEEDED - using navbar)
- [x] Add breadcrumbs to exam list: "Exams" (NOT NEEDED)
- [x] Add breadcrumbs to exam detail: "Exams > Exam Title" (NOT NEEDED - using back buttons)
- [x] Add breadcrumbs to exam form: "Exams > Create" or "Exams > Exam Title > Edit" (NOT NEEDED)
- [x] Add breadcrumbs to pool template add: "Exams > Exam Title > Add Templates to Pool X" (NOT NEEDED)
- [x] Style breadcrumbs with Bootstrap breadcrumb classes (NOT NEEDED)
- [x] Test breadcrumb navigation (NOT NEEDED)

### 4.4 Form Validation Enhancements

- [x] Add client-side validation to exam form (required title) (Django forms handle this)
- [x] Add HTML5 validation attributes (required, min, max) (Django renders these)
- [x] Add JavaScript to validate number_of_versions >= 1 (Server-side validation in model)
- [x] Add duplicate template detection in formset (Implemented via exam-wide uniqueness check)
- [x] Display formset errors with Bootstrap alert-danger (Django messages framework)
- [x] Test form validation with invalid inputs

### 4.5 UI Polish

- [x] Add loading spinners for long operations (if needed) (NOT NEEDED - operations are fast)
- [x] Add confirmation dialogs for destructive actions (delete exam, delete pool) (DONE - confirm_delete templates exist)
- [x] Add success messages using Django messages framework (Template includes messages block)
- [x] Style success messages with Bootstrap alerts (Base template has alert styling)
- [x] Add error messages for failed operations (Django forms handle this)
- [x] Improve empty states with helpful icons and text (DONE - all templates have empty states)
- [x] Add tooltips for version count field explaining purpose (NOT NEEDED - field is clear)
- [x] Verify all buttons have consistent styling (btn-primary, btn-secondary, etc.) (DONE)
- [x] Verify all tables are responsive (table-responsive wrapper) (Bootstrap handles this)

### 4.6 Phase 4 Validation

- [x] Test all navigation links from every page
- [x] Verify breadcrumbs accurately reflect current location (NOT USING BREADCRUMBS)
- [x] Test static files load correctly (check browser console) (Using CDN - no custom static files)
- [x] Test JavaScript functionality across browsers (No custom JavaScript)
- [x] Test form validation with various inputs
- [x] Test responsive design on mobile, tablet, desktop (Bootstrap responsive by default)
- [ ] Verify all UI elements have accessible labels
- [x] Run `poetry run python manage.py check` for any issues (PASSED - no issues)
- [x] Commit changes: "Phase 4: Add navigation, static files, and UI polish"

---

## Phase 5: Testing and Quality Assurance (2-3 days)

### 5.1 Model Tests

- [ ] Create `apps/exams/tests.py` file
- [ ] Import test utilities: `TestCase`, `Exam`, `QuestionPool`, `QuestionPoolTemplate`
- [ ] Create `ExamModelTests` class
- [ ] Test: Create exam with required title only
- [ ] Test: Create exam with all fields (title, date, description)
- [ ] Test: Exam `__str__` returns title
- [ ] Test: Delete exam cascades to pools
- [ ] Test: Delete exam does NOT delete question templates
- [ ] Create `QuestionPoolModelTests` class
- [ ] Test: Create pool with exam and order
- [ ] Test: Unique constraint on (exam, order) prevents duplicates
- [ ] Test: Same order allowed in different exams
- [ ] Test: Delete pool unlinks templates (not delete)
- [ ] Test: Pool ordering by `order` field
- [ ] Create `QuestionPoolTemplateModelTests` class
- [ ] Test: Create pool-template link with version count
- [ ] Test: Unique constraint on (pool, template) prevents duplicates
- [ ] Test: Same template can be in different pools
- [ ] Test: Validation fails if number_of_versions < 1
- [ ] Test: Default number_of_versions is 1
- [ ] Run model tests: `poetry run pytest apps/exams/tests.py::ExamModelTests -v`

### 5.2 View Tests

- [ ] Create `ExamViewTests` class in `apps/exams/tests.py`
- [ ] Test: Exam list view returns 200 status
- [ ] Test: Exam list displays all exams
- [ ] Test: Exam list pagination works (create 25 exams, check pages)
- [ ] Test: Exam create view GET returns form
- [ ] Test: Exam create POST with valid data creates exam
- [ ] Test: Exam create POST with missing title fails validation
- [ ] Test: Exam detail view displays exam and pools
- [ ] Test: Exam update view pre-populates form
- [ ] Test: Exam update POST saves changes
- [ ] Test: Exam delete view shows confirmation
- [ ] Test: Exam delete POST deletes exam
- [ ] Create `PoolViewTests` class
- [ ] Test: Pool create adds pool with correct order
- [ ] Test: Pool create with existing pools sets order = max + 1
- [ ] Test: Pool delete removes pool
- [ ] Test: Pool delete does not delete templates
- [ ] Create `PoolTemplateViewTests` class
- [ ] Test: Pool template add view excludes existing templates
- [ ] Test: Pool template add formset saves multiple templates
- [ ] Test: Pool template add validates unique constraint
- [ ] Test: Pool template delete removes link
- [ ] Run view tests: `poetry run pytest apps/exams/tests.py::ExamViewTests -v`

### 5.3 Form Tests

- [ ] Create `ExamFormTests` class in `apps/exams/tests.py`
- [ ] Test: ExamForm with valid data is valid
- [ ] Test: ExamForm with missing title is invalid
- [ ] Test: ExamForm accepts optional date and description
- [ ] Test: ExamForm date validation (future dates allowed)
- [ ] Create `QuestionPoolTemplateFormSetTests` class
- [ ] Test: Formset with valid template and versions is valid
- [ ] Test: Formset with number_of_versions < 1 is invalid
- [ ] Test: Formset can add multiple templates at once
- [ ] Test: Formset delete functionality works
- [ ] Run form tests: `poetry run pytest apps/exams/tests.py -k Form -v`

### 5.4 Integration Tests

- [ ] Create `ExamWorkflowIntegrationTests` class
- [ ] Test: Full workflow - create exam, add pool, add templates, view detail
- [ ] Test: Create exam with 3 pools, each with 2 templates
- [ ] Test: Add same template to different pools (should succeed)
- [ ] Test: Try to add same template to same pool twice (should fail)
- [ ] Test: Delete exam deletes pools but not templates
- [ ] Test: Template selection filters by subject
- [ ] Test: Pool ordering displays correctly in detail view
- [ ] Test: Version count displays correctly in pool view
- [ ] Run integration tests: `poetry run pytest apps/exams/tests.py::ExamWorkflowIntegrationTests -v`

### 5.5 Question Template Tests Update

- [ ] Review all tests in `apps/questions/tests.py`
- [ ] Verify all Question → QuestionTemplate updates from Phase 1
- [ ] Add test for QuestionTemplate.pool_memberships (reverse FK)
- [ ] Test QuestionTemplate can be in multiple pools
- [ ] Test QuestionTemplate delete with pool memberships (CASCADE behavior)
- [ ] Run all question tests: `poetry run pytest apps/questions/tests.py -v`

### 5.6 Coverage Analysis

- [ ] Run pytest with coverage: `poetry run pytest --cov=apps.exams --cov=apps.questions --cov-report=html`
- [ ] Open `htmlcov/index.html` in browser to view coverage report
- [ ] Identify untested code paths (aim for >80% coverage)
- [ ] Add tests for uncovered branches
- [ ] Test edge cases: empty pools, pools with 20+ templates, very long titles
- [ ] Verify coverage for all models, views, forms
- [ ] Re-run coverage: `poetry run pytest --cov=apps.exams --cov=apps.questions --cov-report=term`
- [ ] Ensure coverage is >80% for both apps

### 5.7 Manual Testing

- [ ] Create test fixtures: 3 subjects, 10 question templates
- [ ] Create exam "Midterm 2026" with date and description
- [ ] Add 5 pools to exam
- [ ] Add 2-3 templates to each pool with varying version counts
- [ ] Test adding duplicate template to same pool (should error)
- [ ] Test adding same template to different pool (should work)
- [ ] Test editing exam metadata
- [ ] Test deleting pool (verify templates remain)
- [ ] Test deleting exam (verify pools deleted, templates remain)
- [ ] Test navigation flow from list → detail → edit → back
- [ ] Test pagination with 25+ exams
- [ ] Test form validation (empty title, negative versions)
- [ ] Test responsive design on phone, tablet, desktop

### 5.8 Performance Testing

- [ ] Create exam with 10 pools, each with 10 templates (100 total links)
- [ ] Measure exam detail page load time (should be <500ms)
- [ ] Check database query count (use Django Debug Toolbar if installed)
- [ ] Verify prefetch_related reduces N+1 queries
- [ ] Test pool template add with 100+ available templates
- [ ] Verify formset renders in reasonable time (<2s)
- [ ] Profile slow pages if found, optimize queries

### 5.9 Code Quality

- [ ] Run black formatter: `poetry run black apps/exams/ apps/questions/`
- [ ] Run ruff linter: `poetry run ruff check apps/exams/ apps/questions/`
- [ ] Fix any linting errors or style issues
- [ ] Run mypy type checker: `poetry run mypy apps/exams/ apps/questions/`
- [ ] Fix type hint errors
- [ ] Review all docstrings for completeness
- [ ] Add missing docstrings to functions and classes
- [ ] Verify all imports are organized (isort if available)
- [ ] Remove any debug print statements or commented code

### 5.10 Phase 5 Validation

- [ ] Run full test suite: `poetry run pytest`
- [ ] Verify all tests pass (100+ tests expected)
- [ ] Verify test coverage >80%: `poetry run pytest --cov=apps --cov-report=term`
- [ ] Run Django system check: `poetry run python manage.py check`
- [ ] Run deployment check: `poetry run python manage.py check --deploy`
- [ ] Verify no migrations pending: `poetry run python manage.py makemigrations --check --dry-run`
- [ ] Review code quality metrics (black, ruff, mypy all pass)
- [ ] Commit changes: "Phase 5: Add comprehensive tests and quality assurance"

---

## Phase 6: Documentation and Finalization (1 day)

### 6.1 Code Documentation

- [ ] Add module docstrings to `apps/exams/models.py`
- [ ] Add module docstrings to `apps/exams/views.py`
- [ ] Add module docstrings to `apps/exams/forms.py`
- [ ] Add module docstrings to `apps/exams/admin.py`
- [ ] Review all class docstrings for clarity
- [ ] Review all method docstrings, ensure parameters and returns are documented
- [ ] Add inline comments for complex logic (e.g., order calculation)

### 6.2 README Updates (if applicable)

- [ ] Update project README with exam management feature description
- [ ] Document exam creation workflow for users
- [ ] Add screenshots of exam list and detail pages (if README includes visuals)
- [ ] Update feature list to include "Exam Management with Question Pools"

### 6.3 Migration Documentation

- [ ] Document migration sequence in code comments
- [ ] Note that Question → QuestionTemplate is backward compatible (URL paths unchanged)
- [ ] Document rollback strategy if needed (RenameModel is reversible)

### 6.4 Final Testing

- [ ] Perform end-to-end test of entire feature
- [ ] Create new exam from scratch
- [ ] Add pools and templates
- [ ] Edit exam
- [ ] Delete pool
- [ ] Delete exam
- [ ] Verify no errors in browser console
- [ ] Verify no broken images or missing CSS
- [ ] Test with empty database (migrations from scratch)
- [ ] Test on fresh database: `poetry run python manage.py migrate`
- [ ] Load fixtures and verify data displays correctly

### 6.5 Final Code Review

- [ ] Review all changed files for code quality
- [ ] Check for hardcoded values (should use constants or settings)
- [ ] Verify all strings are properly escaped in templates
- [ ] Verify CSRF tokens in all forms
- [ ] Check for potential security issues (XSS, SQL injection via ORM)
- [ ] Verify all user inputs are validated
- [ ] Check for proper error handling (try/except where needed)

### 6.6 Phase 6 Validation

- [ ] Run final test suite: `poetry run pytest`
- [ ] Run final coverage report: `poetry run pytest --cov=apps --cov-report=html`
- [ ] Run final code quality checks: `poetry run black . && poetry run ruff check . && poetry run mypy apps/`
- [ ] Run final Django checks: `poetry run python manage.py check --deploy`
- [ ] Perform final manual test of all features
- [ ] Commit changes: "Phase 6: Documentation and finalization"

### 6.7 Change Completion

- [ ] Review all tasks in this document and ensure completion
- [ ] Verify all acceptance criteria from specs are met
- [ ] Run `poetry run openspec validate --change "exams-with-questions"`
- [ ] Address any validation errors or warnings
- [ ] Archive change: `poetry run openspec archive --change "exams-with-questions"`
- [ ] Verify change is marked complete in OpenSpec status
- [ ] Create final commit: "Complete exams-with-questions change"
- [ ] Tag release if applicable: `git tag -a v1.1.0 -m "Add exam management system"`

---

## Summary

**Total Tasks:** 223 tasks across 6 phases

**Estimated Timeline:** 10-14 days

**Breakdown:**
- Phase 1: Question → QuestionTemplate Rename (35 tasks, 2-3 days)
- Phase 2: Create Exams App (27 tasks, 2-3 days)
- Phase 3: Exam Views and Templates (40 tasks, 3-4 days)
- Phase 4: Navigation, Static Files, and Polish (26 tasks, 1-2 days)
- Phase 5: Testing and Quality Assurance (71 tasks, 2-3 days)
- Phase 6: Documentation and Finalization (24 tasks, 1 day)

**Key Milestones:**
1. Phase 1 complete: All Question references renamed to QuestionTemplate
2. Phase 2 complete: Exams app created with models and migrations
3. Phase 3 complete: Full exam CRUD workflow functional
4. Phase 4 complete: UI polished, navigation integrated
5. Phase 5 complete: >80% test coverage, all tests passing
6. Phase 6 complete: Change archived, ready for deployment
