# Specification: Multilingual Question System

**ID:** 003-multilingual-questions  
**Status:** Implemented  
**Version:** 1.0  
**Last Updated:** 2026-02-03  
**Change:** 002-multilingual-questions (archived)

## Overview

Multilingual quiz question system with marker-based text input, JSONField storage, intelligent language fallback, and markdown rendering. Questions have multiple-choice answers with the first choice (order=0) always being correct by convention.

## Purpose

- Create quiz questions in multiple languages
- Support language-independent content (e.g., mathematical notation)
- Provide user-friendly text input with `==lang==` markers
- Render markdown for formatted text
- Manage multiple-choice answers with visual editing
- Enable subject-based filtering and organization

## Data Models

### Location
`apps/questions/models.py`

### Question Model

```python
class Question(UUIDModel):
    """Quiz question with multilingual support."""
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='questions'
    )
    title = models.CharField(
        max_length=200,
        default='no title'
    )
    text = models.JSONField(
        validators=[validate_multilingual_text]
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', '-created_at'])
        ]
```

### Choice Model

```python
class Choice(UUIDModel):
    """Multiple choice option with multilingual support."""
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.JSONField(
        validators=[validate_multilingual_text]
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']
```

### JSON Structure

```json
{
    "none": "Language-independent text",
    "en": "English text",
    "pt": "Portuguese text"
}
```

**Special key:** `"none"` represents language-independent content (formulas, numbers, etc.)

## Multilingual Text System

### Validation

```python
def validate_multilingual_text(value):
    """Validate multilingual text JSON structure."""
    if not isinstance(value, dict):
        raise ValidationError("Must be a dictionary")
    if not value:
        raise ValidationError("Must provide text in at least one language")
    for key, text in value.items():
        if not isinstance(text, str) or not text.strip():
            raise ValidationError(f"Text for '{key}' must be non-empty string")
```

### Fallback Logic

```python
def get_text(self, language_code: str = None) -> str:
    """
    Get text with intelligent fallback.
    
    Fallback order:
    1. Requested language (if specified and exists)
    2. Language-independent version ("none" key)
    3. First available language (alphabetically)
    """
    if language_code and language_code in self.text:
        return self.text[language_code]
    if 'none' in self.text:
        return self.text['none']
    available = sorted(self.text.keys())
    if available:
        return self.text[available[0]]
    raise ValueError("No text available")
```

### Marker Format Input

**User Input:**
```
==en==
What is the sum of 4 and 5?

==pt==
Quanto é 4 + 5?
```

**Stored JSON:**
```json
{
    "en": "What is the sum of 4 and 5?",
    "pt": "Quanto é 4 + 5?"
}
```

**Language-independent (no markers):**
```
4 + 5 = ?
```
Stored as: `{"none": "4 + 5 = ?"}`

## Forms

### MultilingualTextField

Custom form field converting between marker format and JSON:

```python
class MultilingualTextField(forms.CharField):
    """Convert between marker format (UI) and JSON (storage)."""
    
    def to_python(self, value):
        """Parse ==lang== markers into JSON dict."""
        # Parses marker format and builds dictionary
        # Plain text without markers → {"none": text}
        
    def prepare_value(self, value):
        """Convert JSON dict to marker format for editing."""
        # Reverses conversion for display in form
```

### QuestionForm

```python
class QuestionForm(forms.ModelForm):
    text = MultilingualTextField(
        widget=forms.Textarea(attrs={'rows': 6}),
        help_text="Use ==en==, ==pt== markers for languages"
    )
    
    class Meta:
        model = Question
        fields = ['title', 'subject', 'text']
```

### ChoiceFormSet

```python
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=['text'],  # order managed by position, not form field
    extra=0,
    can_delete=False,  # Handled via JavaScript
    min_num=2,
    validate_min=True
)
```

## Custom Choice Management

### JavaScript Functionality

**Location:** `apps/questions/static/questions/js/question_form.js`

**Features:**
- Add choice button (appends new choice from template)
- Delete choice button (minimum 2 enforced)
- Move up/down buttons (reorder choices)
- Automatic form field renumbering on reorder
- Dynamic correct answer badge on first choice

**Key Functions:**
```javascript
function renumberForms() {
    // Updates all input name/id attributes when choices move
    // choices-X- → choices-{index}-
}

function updateChoiceNumbers() {
    // Updates choice numbering badges
    // Shows/hides correct answer badge (first only)
    // Enables/disables move buttons
}
```

**Convention:** First choice (order=0) is always the correct answer. JavaScript visually indicates this with a green badge.

## Markdown Rendering

### Template Tag

**Location:** `apps/questions/templatetags/question_tags.py`

```python
@register.filter
def markdown(text):
    """Convert markdown to safe HTML."""
    return mark_safe(markdown_lib.markdown(
        text,
        extensions=['nl2br', 'fenced_code', 'tables', 'sane_lists']
    ))
```

### Extensions
- `nl2br`: Converts line breaks to `<br>` tags
- `fenced_code`: Supports ```code blocks```
- `tables`: Markdown table support
- `sane_lists`: Better list handling

### Usage
```django
{{ question.text|get_item:lang|markdown }}
```

## URL Patterns

```python
urlpatterns = [
    path('', QuestionListView.as_view(), name='list'),
    path('create/', QuestionCreateView.as_view(), name='create'),
    path('<uuid:pk>/', QuestionPreviewView.as_view(), name='preview'),
    path('<uuid:pk>/edit/', QuestionUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', QuestionDeleteView.as_view(), name='delete'),
]
```

## Views

### QuestionListView
- **Template:** `questions/question_list.html`
- **Filters:** Subject dropdown, include sub-subjects checkbox
- **Auto-filter:** JavaScript auto-submits on selection change
- **Display:** Title, truncated text, subject, choice count, languages, actions
- **Pagination:** Yes

### QuestionCreateView / QuestionUpdateView
- **Template:** `questions/question_form.html`
- **Custom Logic:** 
  - `_extract_choices_from_post()`: Parses choice data from POST
  - `_save_choices()`: Saves choices with correct order
  - `_parse_multilingual_text()`: Converts marker format
- **Subject Pre-fill:** From `?subject=<uuid>` query parameter
- **Redirect:** Preview page after save

### QuestionPreviewView
- **Template:** `questions/question_preview.html`
- **Display:** 
  - Question title and info (subject, dates, choice count)
  - Language cards showing all available translations
  - Markdown-rendered text
  - All choices with correct answer highlighted
  - Fallback indicators

### QuestionDeleteView
- **Template:** `questions/question_confirm_delete.html`
- **Cascade:** Automatically deletes all choices (CASCADE)
- **Display:** Question title, text, choice count warning

## UI Components

### Question List Auto-Filter

**JavaScript:** `apps/questions/static/questions/js/question_list.js`

```javascript
// Auto-submit form when subject dropdown or checkbox changes
subjectSelect.addEventListener('change', () => filterForm.submit());
includeSubCheckbox.addEventListener('change', () => filterForm.submit());
```

No "Apply Filter" button needed - filters apply immediately.

### Question Form Template

**Structure:**
1. Title input field
2. Subject selector
3. Question text textarea (marker format)
4. Choice formset container with:
   - HTML5 `<template>` for new choices
   - Dynamic choice cards with move/delete buttons
   - Correct answer badge on first choice
5. "Add Choice" button
6. Save/Cancel buttons

### Question Preview Cards

**Layout:** Bootstrap cards for each language version
- Header shows language code or "Language Independent"
- Question text rendered with markdown
- Numbered choice list with correct answer highlighted green
- Fallback indicators when using non-preferred language

## Admin Interface

```python
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'choice_count', 'created_at']
    list_filter = ['subject', 'created_at']
    search_fields = ['title', 'text']
    inlines = [ChoiceInline]
    
    fieldsets = [
        ('Question Information', {
            'fields': ['title', 'subject', 'text']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['get_text_preview', 'question', 'order', 'is_correct']
    list_filter = ['question__subject']
```

## Testing

### Test Coverage
- **Total Tests:** 27
- **Model Coverage:** 91%
- **Test File:** `apps/questions/tests.py`

### Test Categories

**Validation Tests:**
```python
def test_valid_multilingual_text()
def test_invalid_not_dict()
def test_invalid_empty_dict()
def test_invalid_empty_string_value()
```

**Model Tests:**
```python
def test_question_creation()
def test_question_str_representation()  # Returns title
def test_get_text_specific_language()
def test_get_text_fallback_to_none()
def test_get_text_fallback_to_any_language()
def test_available_languages()
def test_choice_count()
def test_correct_choice_property()  # First choice (order=0)
def test_question_subject_protect()  # Cannot delete subject
```

**Choice Tests:**
```python
def test_choice_creation()
def test_choice_ordering()
def test_is_correct_property()  # True if order=0
def test_choice_cascade_delete()  # Deleted with question
```

## Static Files Organization

### Django Compressor Integration

**Base Template:**
```django
{% load compress %}
{% compress css %}
    <link rel="stylesheet" href="{% static 'common/css/main.css' %}">
    {% block extra_css %}{% endblock %}
{% endcompress %}

{% compress js %}
    <script src="{% static 'common/js/main.js' %}" defer></script>
    {% block extra_js %}{% endblock %}
{% endcompress %}
```

**App-Specific Files:**
- `apps/common/static/common/js/main.js` - Alert auto-dismiss
- `apps/questions/static/questions/js/question_form.js` - Choice management
- `apps/questions/static/questions/js/question_list.js` - Auto-filter

**Defer Attribute:** All JavaScript loads with `defer`, eliminating need for `DOMContentLoaded` wrappers.

## Conventions

### Correct Answer
**Convention:** The first choice (order=0) is **always** the correct answer.

**Rationale:**
- Simplifies data model (no separate `is_correct` boolean field)
- Clear and consistent rule
- Choice randomization will be handled at quiz display time (future feature)

### Language Keys
- `"none"`: Language-independent content
- `"en"`, `"pt"`, `"es"`, etc.: ISO 639-1 language codes
- Fallback order ensures content always displays

## Performance Considerations

### Database
- Index on `(subject, -created_at)` for filtered lists
- JSONField querying limited in SQLite (use PostgreSQL for production)

### Queries
- `select_related('subject')` for question lists
- `prefetch_related('choices')` for preview display

### Future Optimization
- Consider JSON indexing for language-based searches (PostgreSQL GIN index)
- Cache rendered markdown output
- Lazy-load choice formset in large questions

## Related Specifications

- [001-uuid-model-system](../001-uuid-model-system/spec.md) - Base model
- [002-subject-hierarchy](../002-subject-hierarchy/spec.md) - Subject organization
- [004-static-asset-management](../004-static-asset-management/spec.md) - Compressor setup

## Future Enhancements

- Variable substitution in question/choice text (003-question-variables)
- Moodle XML export functionality
- Choice randomization for quiz display
- Rich text editor alternative to markdown
- Question import from various formats
- Multiple correct answers support
- Question difficulty levels

## References

- Django JSONField: https://docs.djangoproject.com/en/6.0/ref/models/fields/#jsonfield
- Python Markdown: https://python-markdown.github.io/
- Django Formsets: https://docs.djangoproject.com/en/6.0/topics/forms/formsets/
