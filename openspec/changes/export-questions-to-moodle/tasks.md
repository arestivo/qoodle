# Implementation Tasks

## Phase 1: Database Models (Day 1)

### Model Changes

- [ ] Add `grading_mode` field to `Exam` model in `apps/exams/models.py`
  - CharField with choices: `[('single', 'Single Choice'), ('multi', 'Multiple Choice')]`
  - Default: `'single'`
  - Help text: "Single: one correct answer. Multi: partial credit tracking."

- [ ] Add `default_grade` field to `QuestionPool` model in `apps/exams/models.py`
  - DecimalField with `max_digits=5`, `decimal_places=2`
  - Default: `Decimal('1.0')`
  - Validators: `[MinValueValidator(Decimal('0.1'))]`
  - Help text: "Point value for questions in this pool"

- [ ] Add `get_grading_mode_display_verbose()` method to `Exam` model
  - Returns detailed description: "Single Choice (100% / -33% fractions)" or "Multiple Choice (70/10 to 75/5 fractions)"

### Migration

- [ ] Run `poetry run python manage.py makemigrations exams` to create migration
- [ ] Review generated migration file for correctness
- [ ] Run `poetry run python manage.py migrate` to apply migration
- [ ] Verify migration with `poetry run python manage.py showmigrations exams`

### Verification

- [ ] Run `poetry run python manage.py shell` and test:
  ```python
  from apps.exams.models import Exam, QuestionPool
  from decimal import Decimal
  
  # Test default grading mode
  exam = Exam.objects.create(title="Test")
  assert exam.grading_mode == 'single'
  
  # Test multi mode
  exam.grading_mode = 'multi'
  exam.save()
  assert exam.get_grading_mode_display() == 'Multiple Choice'
  
  # Test default grade
  pool = QuestionPool.objects.create(exam=exam, order=1)
  assert pool.default_grade == Decimal('1.0')
  ```

## Phase 2: Export Logic (Days 2-4)

### Core Export Module

- [ ] Create new file `apps/exams/moodle_export.py` (empty file to start)

- [ ] Implement `calculate_fractions()` function in `apps/exams/moodle_export.py`
  ```python
  def calculate_fractions(num_choices: int, grading_mode: str) -> dict[str, Decimal]:
      """Calculate answer fractions for Moodle export."""
  ```
  - Single mode calculates: `wrong = -100 / (num_choices - 1)`, returns `{'correct': Decimal('100.0'), 'wrong': Decimal(str(wrong))}`
  - Multi mode returns hardcoded schemes for 2-6 choices (90/10, 80/10, 70/10, 60/10, 75/5)
  - Raises `ValueError` for <2 choices (any mode)
  - Raises `ValueError` for >6 choices in multi mode

- [ ] Implement `format_html_for_moodle()` function in `apps/exams/moodle_export.py`
  ```python
  def format_html_for_moodle(markdown_text: str) -> str:
      """Convert markdown to HTML with CDATA escaping."""
  ```
  - Use `markdown.Markdown(extensions=['nl2br', 'fenced_code', 'tables', 'sane_lists'])`
  - Replace `']]>'` with `']]&gt;'` to prevent CDATA injection

- [ ] Implement `extract_language_text()` function in `apps/exams/moodle_export.py`
  ```python
  def extract_language_text(json_text: dict, language: str) -> str:
      """Extract language-specific text with fallback logic."""
  ```
  - Check for `json_text[language]`
  - Fall back to first available language if target not found
  - Return first language key as default

### Variable Substitution

- [ ] Implement `generate_variable_value()` function in `apps/exams/moodle_export.py`
  ```python
  def generate_variable_value(config: dict, rng: random.Random) -> Any:
      """Generate random value based on variable config."""
  ```
  - Support types: `integer`, `float`, `choice`
  - Use provided random.Random instance for seeding

- [ ] Implement `substitute_markers()` function in `apps/exams/moodle_export.py`
  ```python
  def substitute_markers(text: str, values: dict[str, Any]) -> str:
      """Replace {{variable}} markers with values."""
  ```
  - Replace all `{{var_name}}` with `str(values[var_name])`

- [ ] Implement `generate_variant()` function in `apps/exams/moodle_export.py`
  ```python
  def generate_variant(
      template: QuestionTemplate,
      version_number: int,
      language: str
  ) -> dict[str, str]:
      """Generate deterministic question variant."""
  ```
  - Create seed: `hash(f"{template.id}_{version_number}")`
  - Use `random.Random(seed)` for deterministic generation
  - Generate variable values using `generate_variable_value()`
  - Substitute markers in question text
  - Return `{'text': ..., 'values': {...}}`

- [ ] Implement `get_choices_for_variant()` function in `apps/exams/moodle_export.py`
  ```python
  def get_choices_for_variant(
      template: QuestionTemplate,
      variant: dict,
      language: str
  ) -> list[dict]:
      """Get answer choices with variable substitution."""
  ```
  - Load choices from `template.choices.all().order_by('order')`
  - Extract language text with `extract_language_text(choice.text, language)`
  - Substitute variables in choice text
  - Mark first choice (order=0) as correct
  - Return list of `{'text': ..., 'is_correct': bool}`

- [ ] Implement `generate_all_variants()` function in `apps/exams/moodle_export.py`
  ```python
  def generate_all_variants(
      template: QuestionTemplate,
      num_versions: int,
      language: str
  ) -> list[dict]:
      """Generate unique question variants with collision detection."""
  ```
  - Try up to 50 attempts to generate unique variants
  - Each attempt adds offset to seed: `f"{template.id}_{version}_{attempt}"`
  - Check uniqueness by comparing rendered text
  - Raise `ValueError` if unable to generate unique set after 50 attempts

### XML Generation

- [ ] Implement `generate_moodle_xml()` function in `apps/exams/moodle_export.py`
  ```python
  def generate_moodle_xml(exam: Exam, language: str) -> str:
      """Generate Moodle XML for exam export."""
  ```
  - Import `xml.etree.ElementTree as ET` and `xml.dom.minidom`
  - Create root `<quiz>` element
  - Iterate through `exam.pools.all().order_by('order')`
  - For each pool, iterate through templates
  - Generate variants using `generate_all_variants()`
  - Create `<question type="multichoice">` elements
  - Add sequential names: Q1, Q2, Q3...
  - Add sequential tags: q1, q2, q3...
  - Wrap question text in `<![CDATA[...]]>`
  - Add answers with fractions from `calculate_fractions()`
  - Add `<single>true</single>` for single-choice mode, `<single>false</single>` for multi-choice
  - Add `<defaultgrade>` from `pool.default_grade`
  - Pretty-print with `minidom.toprettyxml(indent="  ")`

### Verification

- [ ] Create test template with variables in Django shell:
  ```python
  from apps.questions.models import QuestionTemplate
  template = QuestionTemplate.objects.create(
      text={'en': 'What is {{x}} + {{y}}?'},
      variables={'x': {'type': 'integer', 'min': 1, 'max': 10}, 
                 'y': {'type': 'integer', 'min': 1, 'max': 10}}
  )
  ```

- [ ] Test variant generation in shell:
  ```python
  from apps.exams.moodle_export import generate_variant
  v0 = generate_variant(template, 0, 'en')
  v1 = generate_variant(template, 1, 'en')
  assert v0['text'] != v1['text']  # Different values
  
  # Test determinism
  v0_again = generate_variant(template, 0, 'en')
  assert v0['text'] == v0_again['text']  # Same seed = same output
  ```

## Phase 3: Views and Forms (Days 5-6)

### Forms

- [ ] Modify `ExamForm` in `apps/exams/forms.py` to include `grading_mode` field
  - Add `'grading_mode'` to `fields` list
  - Widget: `forms.RadioSelect()`

- [ ] Create `PoolGradeForm` in `apps/exams/forms.py`
  - ModelForm for QuestionPool
  - Fields: `['default_grade']`
  - Widget: `forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1'})`

### Views

- [ ] Create `ExamExportView` in `apps/exams/views.py`
  ```python
  class ExamExportView(View):
      """Export exam to Moodle XML format."""
      def post(self, request, pk): ...
  ```
  - Get exam or 404
  - Get language from POST data (default: 'en')
  - Call `generate_moodle_xml(exam, language)` with try/except
  - On ValueError, add error message and redirect to detail
  - Return HttpResponse with `content_type='application/xml'`
  - Set filename: `{exam_title}_{language}.xml`
  - Content-Disposition: `attachment`

- [ ] Create `PoolUpdateGradeView` in `apps/exams/views.py`
  ```python
  class PoolUpdateGradeView(UpdateView):
      """Update default grade for question pool."""
  ```
  - Model: QuestionPool
  - Form: PoolGradeForm
  - Success URL: exam detail page
  - Add success message: "Pool {order} grade updated to {grade} points"

### URLs

- [ ] Add export route to `apps/exams/urls.py`:
  ```python
  path('<uuid:pk>/export/', ExamExportView.as_view(), name='export')
  ```

- [ ] Add pool grade update route to `apps/exams/urls.py`:
  ```python
  path('<uuid:exam_pk>/pool/<uuid:pk>/grade/', 
       PoolUpdateGradeView.as_view(), 
       name='pool_update_grade')
  ```

### Templates

- [ ] Modify `apps/exams/templates/exams/exam_form.html` to add grading mode section
  - Add form section after description field
  - Two radio buttons (single/multi) with FontAwesome icons
  - Single: `<i class="fas fa-check-circle text-primary"></i>`
  - Multi: `<i class="fas fa-tasks text-success"></i>`
  - Include descriptive help text for each option
  - Show help text explaining fraction schemes

- [ ] Modify `apps/exams/templates/exams/exam_detail.html` to add export form
  - Add export form after exam header
  - Language dropdown with options: English, Português
  - Submit button: `<i class="fas fa-download"></i> Export to Moodle`
  - Use Bootstrap `input-group` for styling
  - Form method: POST to `{% url 'exams:export' exam.pk %}`

- [ ] Modify `apps/exams/templates/exams/exam_detail.html` to show grading mode badge
  - Add badge below title and date
  - Single: `<span class="badge bg-primary"><i class="fas fa-check-circle"></i> Single Choice</span>`
  - Multi: `<span class="badge bg-success"><i class="fas fa-tasks"></i> Multiple Choice</span>`

- [ ] Modify `apps/exams/templates/exams/exam_detail.html` to show pool grades
  - Add badge next to pool order: `<span class="badge bg-secondary">{{ pool.default_grade }} points</span>`
  - Add edit button with modal trigger: `<i class="fas fa-edit"></i> Edit Grade`

- [ ] Modify `apps/exams/templates/exams/exam_detail.html` to add pool grade edit modal
  - Bootstrap modal with form
  - Form posts to `{% url 'exams:pool_update_grade' exam.pk pool.pk %}`
  - Number input for default_grade (step=0.1, min=0.1)
  - Save button with icon: `<i class="fas fa-save"></i> Save`

### Verification

- [ ] Run development server: `poetry run python manage.py runserver`

- [ ] Test grading mode UI:
  - Navigate to exam create page
  - Verify "Single Choice" is selected by default
  - Select "Multiple Choice" radio button
  - Submit form and verify saved correctly

- [ ] Test export UI:
  - Navigate to exam detail page
  - Verify grading mode badge displays
  - Select language from dropdown
  - Click "Export to Moodle" button
  - Verify XML file downloads with correct filename

- [ ] Test pool grade UI:
  - Click "Edit Grade" button on pool
  - Change default_grade to 2.5
  - Submit modal form
  - Verify badge updates to "2.5 points"

## Phase 4: Testing (Days 7-8)

### Unit Tests for Export Logic

- [ ] Create test class `CalculateFractionsTests` in `apps/exams/tests.py`
  - Test single mode with 2 choices returns 100/-100
  - Test single mode with 3 choices returns 100/-50
  - Test single mode with 4 choices returns 100/-33.33
  - Test single mode with 5 choices returns 100/-25
  - Test single mode with 6 choices returns 100/-20
  - Test multi mode schemes for 2, 3, 4, 5, 6 choices (90/10, 80/10, 70/10, 60/10, 75/5)
  - Test ValueError raised for <2 choices (any mode)
  - Test ValueError raised for 7+ choices in multi mode

- [ ] Create test class `VariantGenerationTests` in `apps/exams/tests.py`
  - Test deterministic generation (same seed = same output)
  - Test different versions generate different values
  - Test integer variable ranges
  - Test float variable with decimals
  - Test choice variable selection
  - Test variable substitution in question text
  - Test variable substitution in choice text

- [ ] Create test class `UniquenessValidationTests` in `apps/exams/tests.py`
  - Test successful uniqueness with wide variable ranges
  - Test ValueError raised when narrow range causes collisions
  - Test error message includes actionable advice

- [ ] Create test class `MoodleXMLGenerationTests` in `apps/exams/tests.py`
  - Test XML structure has `<quiz>` root element
  - Test question elements have correct type="multichoice"
  - Test sequential naming (Q1, Q2, Q3...)
  - Test sequential tagging (q1, q2, q3...)
  - Test CDATA wrapping for question text
  - Test fraction attributes on answer elements
  - Test `<single>true</single>` for single-choice exams
  - Test `<single>false</single>` for multi-choice exams
  - Test defaultgrade element matches pool.default_grade

- [ ] Create test class `LanguageExtractionTests` in `apps/exams/tests.py`
  - Test extraction of specified language
  - Test fallback to first available language
  - Test fallback when target language missing

- [ ] Create test class `MarkdownConversionTests` in `apps/exams/tests.py`
  - Test code blocks convert correctly
  - Test lists convert correctly
  - Test tables convert correctly
  - Test `]]>` is escaped to `]]&gt;`

### Integration Tests

- [ ] Create test class `ExamExportViewTests` in `apps/exams/tests.py`
  - Test GET request returns 405 (method not allowed)
  - Test POST returns XML file download
  - Test filename format: `{title}_{language}.xml`
  - Test Content-Type header is `application/xml`
  - Test Content-Disposition header is `attachment`
  - Test error handling when exam not found

- [ ] Create test class `PoolGradeUpdateTests` in `apps/exams/tests.py`
  - Test successful grade update
  - Test redirect to exam detail after save
  - Test success message displayed
  - Test validation error for grade < 0.1

- [ ] Create test class `GradingModeFormTests` in `apps/exams/tests.py`
  - Test default value is 'single'
  - Test both choices appear in form
  - Test RadioSelect widget is used

### End-to-End Validation

- [ ] Create test exam in Django admin with:
  - 3 question pools
  - 2 templates per pool (one with variables, one without)
  - 3 versions per template with variables
  - Total: 12 questions (3 pools × (1×3 + 1×1))

- [ ] Export exam and validate XML:
  - Run export through UI
  - Save XML to file
  - Validate with `xmllint --noout {filename}.xml` (if available)
  - Check file opens correctly in text editor
  - Verify question count matches expected (12)

- [ ] Test Moodle import (if test instance available):
  - Log into Moodle test instance
  - Navigate to question bank
  - Import XML file
  - Verify all questions imported successfully
  - Check question text renders correctly
  - Verify answer fractions match expected values

### Coverage Check

- [ ] Run test suite with coverage: `poetry run pytest --cov=apps/exams --cov-report=term-missing`
- [ ] Verify coverage is >80% for `apps/exams/moodle_export.py`
- [ ] Verify coverage is >80% for export-related views
- [ ] Add additional tests for any uncovered lines

## Phase 5: Error Handling and Polish (Day 9)

### Error Handling

- [ ] Add error handling for empty exams in `ExamExportView`
  - Check if exam has no pools
  - Show error message: "Cannot export exam with no question pools"
  - Redirect to exam detail

- [ ] Add error handling for pools with no templates
  - Check if any pool has zero templates
  - Show error message: "Pool {order} has no templates"
  - Redirect to exam detail

- [ ] Add error handling for templates with no choices
  - Check if template has zero choices
  - Show error message: "Template '{title}' has no answer choices"
  - Redirect to exam detail

- [ ] Add user-friendly error messages for variant generation failures
  - Catch ValueError from `generate_all_variants()`
  - Show Django message: "Unable to generate unique variants for template '{title}'. Try widening variable ranges or reducing number of versions."
  - Redirect to exam detail

- [ ] Add user-friendly error for >6 choices in multi mode
  - Catch ValueError from `calculate_fractions()`
  - Show Django message: "Multi-choice grading only supports 2-6 answer choices. Template '{title}' has {num} choices. Please use single-choice mode or reduce answers."
  - Redirect to exam detail

### Documentation

- [ ] Add docstrings to all functions in `apps/exams/moodle_export.py`
  - Include type hints
  - Document parameters and return values
  - Include usage examples for key functions

- [ ] Add help text to grading mode field explaining fraction schemes
  - Single: "One correct answer with -33% penalty for wrong selections"
  - Multi: "Custom fractions (70/10 to 75/5) for answer pattern tracking"

- [ ] Add inline documentation in templates explaining export workflow
  - Comment explaining CDATA requirement
  - Comment explaining sequential naming (Q1, Q2...)

### UI Polish

- [ ] Add loading state to export button
  - Use JavaScript to disable button on click
  - Change button text to "Generating..." with spinner icon
  - Prevent double-submission

- [ ] Add help text to language dropdown
  - Explain language selection applies to all questions
  - Show available languages based on exam content

- [ ] Style error messages with Bootstrap alerts
  - Use `alert-danger` class for errors
  - Include icon: `<i class="fas fa-exclamation-triangle"></i>`

- [ ] Add confirmation for pool grade changes
  - Show current value in modal
  - Highlight changed value after save

### Final Verification

- [ ] Run full test suite: `poetry run pytest`
  - All tests pass
  - Coverage >80%

- [ ] Run linters:
  - `poetry run black apps/exams/` (format code)
  - `poetry run ruff check apps/exams/` (check style)
  - `poetry run mypy apps/exams/` (type check)

- [ ] Manual testing checklist:
  - [ ] Create exam with single-choice mode (4 choices)
  - [ ] Export and verify fractions are 100/-33.33 and `<single>true</single>`
  - [ ] Create exam with single-choice mode (2 choices)
  - [ ] Export and verify fractions are 100/-100
  - [ ] Create exam with multi-choice mode (4 choices)
  - [ ] Export and verify fractions are 70/10 and `<single>false</single>`
  - [ ] Create template with variables
  - [ ] Export and verify variants are unique and deterministic
  - [ ] Test language selection (English and Português)
  - [ ] Test pool grade editing
  - [ ] Test error cases (empty exam, narrow variable range, >6 choices)

- [ ] Update project documentation
  - Add section to README about Moodle export feature
  - Document grading mode options
  - Provide example variable configuration

- [ ] Git commit all changes:
  ```bash
  git add apps/exams/
  git commit -m "Implement Moodle XML export feature
  
  - Add grading_mode field to Exam model
  - Add default_grade field to QuestionPool model
  - Implement variant generation with seeded random
  - Implement XML export with CDATA wrapping
  - Add export view with language selection
  - Add pool grade editing UI
  - Tests with >80% coverage"
  ```

## Summary

**Total Tasks:** 85
- Phase 1 (Models): 9 tasks
- Phase 2 (Export Logic): 20 tasks
- Phase 3 (Views/UI): 19 tasks
- Phase 4 (Testing): 22 tasks
- Phase 5 (Polish): 15 tasks

**Estimated Timeline:** 9 days
- Days 1: Database models and migrations
- Days 2-4: Core export logic and variant generation
- Days 5-6: Views, forms, and UI templates
- Days 7-8: Comprehensive testing
- Day 9: Error handling, documentation, and polish
