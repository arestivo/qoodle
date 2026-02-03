# Specification: Testing Infrastructure

**ID:** 005-testing-infrastructure  
**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** 2026-02-03  
**Change:** N/A (foundational infrastructure)

## Overview

pytest-django testing framework with comprehensive coverage requirements (>80%), organized by Django app. Each app contains `tests.py` with model, view, form, and integration tests. All terminal commands use `poetry run` prefix for consistent environment management.

## Purpose

- Ensure code quality through automated testing
- Maintain high test coverage (>80% minimum)
- Provide fast, reliable test execution
- Enable test-driven development (TDD)
- Catch regressions early
- Document expected behavior through tests

## Framework

### pytest-django

**Why pytest instead of Django's TestCase:**
- Simpler fixture system
- Better parameterization
- More readable assertions
- Powerful plugin ecosystem
- Faster test discovery

### Configuration

**File:** `pytest.ini` (project root)

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = 
    --reuse-db
    --strict-markers
    --tb=short
    --cov=apps
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

### Coverage Requirements

**Minimum:** 80% overall coverage  
**Target:** 90%+ for critical apps  
**Enforcement:** CI pipeline fails if coverage < 80%

**Generated Reports:**
- Terminal: Shows missing lines during test run
- HTML: `htmlcov/index.html` for detailed browsing

## Test Organization

### Directory Structure

```
qoodle-ui/
├── apps/
│   ├── common/
│   │   └── tests.py            # 5 tests, UUIDModel coverage
│   ├── subjects/
│   │   └── tests.py            # 18 tests, 99% coverage
│   └── questions/
│       └── tests.py            # 27 tests, 91% coverage
└── pytest.ini
```

**Convention:** Each app has single `tests.py` file (not `tests/` directory).

### Test File Template

```python
# apps/myapp/tests.py

import pytest
from django.urls import reverse
from apps.myapp.models import MyModel

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def my_model_instance():
    """Create a test instance of MyModel."""
    return MyModel.objects.create(name="Test")

# ============================================================
# Model Tests
# ============================================================

@pytest.mark.django_db
class TestMyModel:
    """Test MyModel functionality."""
    
    def test_creation(self, my_model_instance):
        """Test model creation with valid data."""
        assert my_model_instance.name == "Test"
        assert my_model_instance.pk is not None

# ============================================================
# View Tests
# ============================================================

@pytest.mark.django_db
class TestMyModelListView:
    """Test MyModelListView."""
    
    def test_list_view_status_code(self, client):
        """Test that list view returns 200."""
        response = client.get(reverse('myapp:list'))
        assert response.status_code == 200

# ============================================================
# Form Tests
# ============================================================

@pytest.mark.django_db
class TestMyModelForm:
    """Test MyModelForm validation."""
    
    def test_valid_form(self):
        """Test form with valid data."""
        form = MyModelForm(data={'name': 'Test'})
        assert form.is_valid()
```

## Running Tests

### All Tests

```bash
poetry run pytest
```

**Output:**
```
apps/common/tests.py .....                                [  8%]
apps/subjects/tests.py ..................                 [ 44%]
apps/questions/tests.py ...........................       [100%]

---------- coverage: platform linux, python 3.12.1 -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
apps/common/models.py                12      0   100%
apps/subjects/models.py              45      0   100%
apps/subjects/views.py               67      1    99%   42
apps/questions/models.py             89      8    91%   23-25, 78-81
---------------------------------------------------------------
TOTAL                               213     9    96%

50 passed in 2.34s
```

### Specific App

```bash
poetry run pytest apps/subjects/tests.py
```

### Specific Test Class

```bash
poetry run pytest apps/subjects/tests.py::TestSubject
```

### Specific Test Method

```bash
poetry run pytest apps/subjects/tests.py::TestSubject::test_creation
```

### With Verbose Output

```bash
poetry run pytest -v
```

### Stop on First Failure

```bash
poetry run pytest -x
```

### Run Only Failed Tests

```bash
poetry run pytest --lf  # Last failed
```

### Skip Slow Tests

```bash
poetry run pytest -m "not slow"
```

## Test Categories

### Model Tests

**Purpose:** Test model creation, validation, properties, relationships

**Example:** `apps/common/tests.py`

```python
@pytest.mark.django_db
class TestUUIDModel:
    """Test UUIDModel abstract base."""
    
    def test_uuid_auto_generation(self, subject):
        """Test that UUID is auto-generated."""
        assert isinstance(subject.id, uuid.UUID)
    
    def test_timestamps_auto_set(self, subject):
        """Test created_at and updated_at are auto-set."""
        assert subject.created_at is not None
        assert subject.updated_at is not None
    
    def test_updated_at_changes(self, subject):
        """Test updated_at changes on save."""
        old_updated = subject.updated_at
        time.sleep(0.01)
        subject.name = "Updated"
        subject.save()
        assert subject.updated_at > old_updated
```

### View Tests

**Purpose:** Test HTTP responses, redirects, context data, permissions

**Example:** `apps/subjects/tests.py`

```python
@pytest.mark.django_db
class TestSubjectListView:
    """Test SubjectListView."""
    
    def test_list_view_status_code(self, client):
        """Test list view returns 200."""
        response = client.get(reverse('subjects:list'))
        assert response.status_code == 200
    
    def test_list_view_uses_correct_template(self, client):
        """Test list view uses correct template."""
        response = client.get(reverse('subjects:list'))
        assert 'subjects/subject_list.html' in [t.name for t in response.templates]
    
    def test_list_view_context_has_subjects(self, client, root_subject):
        """Test subjects are in context."""
        response = client.get(reverse('subjects:list'))
        assert 'subjects' in response.context
        assert root_subject in response.context['subjects']
```

### Form Tests

**Purpose:** Test form validation, cleaning, custom logic

**Example:** `apps/questions/tests.py`

```python
@pytest.mark.django_db
class TestQuestionForm:
    """Test QuestionForm validation."""
    
    def test_valid_multilingual_text(self, subject):
        """Test form accepts valid marker format."""
        data = {
            'title': 'Test Question',
            'subject': subject.id,
            'text': '==en==\nEnglish text\n==pt==\nPortuguese text'
        }
        form = QuestionForm(data=data)
        assert form.is_valid()
    
    def test_invalid_empty_text(self, subject):
        """Test form rejects empty text."""
        data = {
            'title': 'Test Question',
            'subject': subject.id,
            'text': ''
        }
        form = QuestionForm(data=data)
        assert not form.is_valid()
        assert 'text' in form.errors
```

### Integration Tests

**Purpose:** Test complete workflows across multiple components

**Example:**

```python
@pytest.mark.django_db
@pytest.mark.integration
class TestQuestionCreateWorkflow:
    """Test complete question creation workflow."""
    
    def test_create_question_with_choices(self, client, subject):
        """Test creating question with multiple choices."""
        url = reverse('questions:create')
        data = {
            'title': 'New Question',
            'subject': subject.id,
            'text': 'What is 2+2?',
            'choices-TOTAL_FORMS': '4',
            'choices-INITIAL_FORMS': '0',
            'choices-0-text': '4',
            'choices-1-text': '3',
            'choices-2-text': '5',
            'choices-3-text': '22',
        }
        response = client.post(url, data)
        
        # Check redirect
        assert response.status_code == 302
        
        # Check question created
        question = Question.objects.get(title='New Question')
        assert question.subject == subject
        
        # Check choices created
        assert question.choices.count() == 4
        assert question.choices.filter(order=0).first().text == {'none': '4'}
```

## Fixtures

### Built-in Django Fixtures

```python
@pytest.mark.django_db
def test_with_client(client):
    """Use Django test client."""
    response = client.get('/')

@pytest.mark.django_db
def test_with_admin_client(admin_client):
    """Use client with admin user logged in."""
    response = admin_client.get('/admin/')

@pytest.mark.django_db
def test_with_rf(rf):
    """Use RequestFactory."""
    request = rf.get('/')
```

### Custom Fixtures

**Location:** `apps/myapp/tests.py` (same file as tests)

```python
@pytest.fixture
def root_subject():
    """Create a root subject."""
    return Subject.objects.create(name="Root", parent=None)

@pytest.fixture
def child_subject(root_subject):
    """Create a child subject."""
    return Subject.objects.create(name="Child", parent=root_subject)

@pytest.fixture
def question_with_choices(root_subject):
    """Create a question with 4 choices."""
    question = Question.objects.create(
        title="Test Question",
        subject=root_subject,
        text={"en": "What is 2+2?"}
    )
    for i, text in enumerate(['4', '3', '5', '22']):
        Choice.objects.create(
            question=question,
            text={'none': text},
            order=i
        )
    return question
```

### Fixture Scope

```python
@pytest.fixture(scope='session')
def db_setup():
    """Run once per test session."""
    # Expensive setup
    pass

@pytest.fixture(scope='module')
def module_data():
    """Run once per module."""
    pass

@pytest.fixture(scope='function')  # Default
def function_data():
    """Run for each test."""
    pass
```

## Coverage Analysis

### Current Coverage (Apps)

| App | Tests | Coverage | Status |
|-----|-------|----------|--------|
| common | 5 | 100% | ✅ Excellent |
| subjects | 18 | 99% | ✅ Excellent |
| questions | 27 | 91% | ✅ Good |

**Total:** 50 tests, 96% overall coverage

### Viewing Coverage Reports

**Terminal:**
```bash
poetry run pytest
# Shows coverage summary with missing lines
```

**HTML Report:**
```bash
poetry run pytest
# Generates htmlcov/index.html
poetry run python -m http.server 8080 --directory htmlcov
# Open http://localhost:8080
```

### Identifying Gaps

**Missing Coverage Example:**
```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
apps/questions/models.py             89      8    91%   23-25, 78-81
```

**Lines 23-25, 78-81 not covered.** Check what those lines do:
```python
# Line 23-25: Error handling edge case
def get_text(self, language_code=None):
    if language_code and language_code in self.text:
        return self.text[language_code]
    # Missing test: What if language_code not in text?
```

**Solution:** Add test for edge case:
```python
def test_get_text_fallback(self, question):
    """Test fallback when requested language not available."""
    question.text = {'en': 'English only'}
    question.save()
    assert question.get_text('pt') == 'English only'  # Fallback
```

## Continuous Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run tests
      run: poetry run pytest
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

**Behavior:**
- Runs on every push and PR
- Fails if coverage < 80%
- Uploads coverage to Codecov (if configured)

## Testing Best Practices

### ✅ Do

- **Arrange-Act-Assert:** Structure tests clearly
  ```python
  def test_something():
      # Arrange
      obj = MyModel.objects.create(name="Test")
      
      # Act
      result = obj.do_something()
      
      # Assert
      assert result == expected
  ```

- **One assertion per test:** Keep tests focused
  ```python
  def test_name_is_set():
      obj = MyModel.objects.create(name="Test")
      assert obj.name == "Test"
  
  def test_slug_is_generated():
      obj = MyModel.objects.create(name="Test")
      assert obj.slug == "test"
  ```

- **Use fixtures:** Avoid duplication
  ```python
  @pytest.fixture
  def user():
      return User.objects.create(username="test")
  
  def test_with_user(user):
      assert user.username == "test"
  ```

- **Descriptive names:** Test names should explain what they test
  ```python
  def test_create_subject_with_parent_sets_parent_relationship()
  def test_delete_subject_with_children_raises_protected_error()
  ```

### ❌ Don't

- **Don't test Django internals:** Trust that `CharField` works
  ```python
  # Bad - testing Django, not our code
  def test_name_field_is_charfield():
      field = Subject._meta.get_field('name')
      assert isinstance(field, models.CharField)
  ```

- **Don't write flaky tests:** Tests should be deterministic
  ```python
  # Bad - depends on current time
  def test_created_recently():
      obj = MyModel.objects.create()
      assert obj.created_at == datetime.now()  # May fail
  
  # Good - test relative time
  def test_created_recently():
      obj = MyModel.objects.create()
      assert (datetime.now() - obj.created_at).seconds < 1
  ```

- **Don't test too much at once:** Keep tests focused
  ```python
  # Bad - testing everything
  def test_question_workflow():
      q = Question.objects.create(...)
      assert q.id is not None
      assert q.title == "Test"
      assert q.choices.count() == 0
      c = Choice.objects.create(...)
      assert q.choices.count() == 1
      # ... etc
  
  # Good - separate tests
  def test_question_creation()
  def test_question_has_no_choices_initially()
  def test_adding_choice_to_question()
  ```

## Database Management

### Test Database

pytest-django automatically:
1. Creates test database
2. Runs migrations
3. Destroys database after tests

**Reuse Database (Faster):**
```bash
poetry run pytest --reuse-db
```

**Recreate Database:**
```bash
poetry run pytest --create-db
```

### Transactions

**Default:** Each test runs in transaction, rolled back after test.

**Disable transaction (if needed):**
```python
@pytest.mark.django_db(transaction=True)
def test_something():
    # Test code that requires real commits
    pass
```

## Debugging Tests

### Print Debug Info

```python
def test_something(subject):
    print(f"Subject: {subject}")  # Use -s flag to see output
    assert subject.name == "Test"
```

```bash
poetry run pytest -s  # Show print output
```

### Drop into debugger

```python
def test_something():
    import pdb; pdb.set_trace()
    # Execution pauses here
    assert True
```

```bash
poetry run pytest --pdb  # Auto-drop into debugger on failure
```

### Show full traceback

```bash
poetry run pytest --tb=long  # Full traceback
poetry run pytest --tb=short  # Short traceback (default)
poetry run pytest --tb=no  # No traceback
```

## Performance Testing

### Mark Slow Tests

```python
@pytest.mark.slow
@pytest.mark.django_db
def test_expensive_operation():
    # Long-running test
    pass
```

**Skip slow tests:**
```bash
poetry run pytest -m "not slow"
```

### Measure Test Duration

```bash
poetry run pytest --durations=10  # Show 10 slowest tests
```

## Related Specifications

- [001-uuid-model-system](../001-uuid-model-system/spec.md) - Model testing patterns
- [002-subject-hierarchy](../002-subject-hierarchy/spec.md) - 99% coverage example
- [003-multilingual-questions](../003-multilingual-questions/spec.md) - 91% coverage example

## Future Enhancements

- Factory pattern for test data (factory_boy)
- Parameterized tests with pytest.mark.parametrize
- Snapshot testing for HTML output
- Performance regression tests
- Browser testing with Selenium/Playwright
- API testing framework (when REST API added)
- Mutation testing (mutpy) to verify test quality

## References

- pytest: https://docs.pytest.org/
- pytest-django: https://pytest-django.readthedocs.io/
- Coverage.py: https://coverage.readthedocs.io/
- Django Testing: https://docs.djangoproject.com/en/6.0/topics/testing/
