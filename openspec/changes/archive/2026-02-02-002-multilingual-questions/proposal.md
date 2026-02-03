# Proposal: Multilingual Questions

## Problem Statement

Teachers need to create quiz questions for their students, with support for multiple languages. Questions must:

- Belong to a subject for organizational purposes
- Have question text and multiple choice options
- Support multiple languages with intelligent fallback
- Allow language-independent content (e.g., mathematical notation)
- Display correctly regardless of which languages are available

Currently, there is no question model or multilingual content system.

## Proposed Solution

### 1. Question Model

Create a `Question` model in new `apps/questions/` app:

```python
class Question(UUIDModel):
    """Quiz question with multilingual support."""
    
    subject = ForeignKey(Subject, on_delete=PROTECT, related_name="questions")
    title = CharField(
        max_length=200,
        default="no title",
        help_text="Short title to identify this question"
    )
    text = JSONField(
        help_text="Question text in multiple languages",
        validators=[validate_multilingual_text]
    )
    
    # Example text JSON structure:
    # {
    #     "none": "What is 4 + 5?",
    #     "en": "What is 4 + 5?",
    #     "pt": "Quanto é 4 + 5?"
    # }
```

**Fields:**
- `subject` - ForeignKey to Subject (PROTECT on delete)
- `title` - CharField for easier identification (mandatory, default "no title")
- `text` - JSONField containing language code → text mappings
- Standard UUIDModel fields (id, created_at, updated_at)

**Methods:**
- `__str__()` - Returns the title for easy identification
- `get_text(language_code)` - Get text for specific language with fallback
- `available_languages()` - Return set of all language codes used
- `get_all_texts()` - Return dict of all language versions
- `choice_count` - Property returning number of choices
- `correct_choice` - Property returning the first choice (order=0)

### 2. Choice Model

Create a `Choice` model for multiple choice options:

```python
class Choice(UUIDModel):
    """
    Multiple choice option with multilingual support.
    
    Important: The first choice (order=0) is always the correct answer.
    When displaying questions to students, choices should be randomized.
    """
    
    question = ForeignKey(Question, on_delete=CASCADE, related_name="choices")
    text = JSONField(
        help_text="Choice text in multiple languages",
        validators=[validate_multilingual_text]
    )
    order = PositiveIntegerField(default=0)
    
    # Example text JSON structure:
    # {
    #     "none": "it's 9",
    #     "en": "it's 9",
    #     "pt": "É 9"
    # }
    
    class Meta:
        ordering = ["order", "created_at"]
```

**Fields:**
- `question` - ForeignKey to Question (CASCADE on delete)
- `text` - JSONField containing language code → text mappings
- `order` - Integer for explicit ordering (default 0)
  - **Convention:** The first choice (order=0) is always the correct answer
  - Other choices are incorrect options (distractors)
- Standard UUIDModel fields

**Methods:**
- `get_text(language_code)` - Get text for specific language with fallback
- `is_correct` - Property that returns True if this is the first choice (order=0)

**Design Note:**  
By convention, the correct answer is always the first choice in storage. When presenting questions to students (future feature), the choices should be randomized to prevent answer pattern recognition. This approach simplifies the model while maintaining flexibility.

### 3. Language Fallback Logic

Implement consistent fallback logic across Question and Choice:

```python
def get_text(self, language_code: str = None) -> str:
    """
    Get text for specific language with fallback.
    
    Fallback order:
    1. Requested language (if specified and exists)
    2. Language-independent version ("none" key)
    3. First available language (alphabetically)
    
    Raises ValueError if no text available in any language.
    """
    if not self.text:
        raise ValueError("No text available")
    
    # Try requested language
    if language_code and language_code in self.text:
        return self.text[language_code]
    
    # Try language-independent
    if "none" in self.text:
        return self.text["none"]
    
    # Fallback to any available language
    available = sorted(self.text.keys())
    if available:
        return self.text[available[0]]
    
    raise ValueError("No text available in any language")
```

### 4. JSON Field Validation

Create custom validator for multilingual JSON fields:

```python
def validate_multilingual_text(value):
    """
    Validate multilingual text JSON structure.
    
    Requirements:
    - Must be a dict
    - Must have at least one language key
    - All values must be non-empty strings
    - Keys should be valid language codes or "none"
    """
    if not isinstance(value, dict):
        raise ValidationError("Multilingual text must be a dictionary")
    
    if not value:
        raise ValidationError("Must provide text in at least one language")
    
    for key, text in value.items():
        if not isinstance(text, str) or not text.strip():
            raise ValidationError(f"Text for language '{key}' must be a non-empty string")
```

### 5. Views

**QuestionListView**
- Display questions filtered by subject
- Include toggle/checkbox to include sub-subject questions
- Show question text (in default/first available language)
- Show choice count per question
- Paginated results

**QuestionCreateView**
- Form with subject selection (pre-filled if coming from subject page)
- Question text input with language tabs/fields
- Inline formset for choices (minimum 2, add more dynamically)
- Each choice has language tabs/fields
- Save creates question + all choices atomically

**QuestionUpdateView**
- Edit question text for all languages
- Edit/add/remove choices
- Change subject
- Maintain language versions

**QuestionDeleteView**
- Confirmation page
- Cascade deletes all choices

**QuestionPreviewView**
- Display question in all available languages side-by-side
- Show all choices for each language
- Highlight which versions are language-independent
- Show fallback logic in action

### 6. Forms

**MultilingualTextField**
```python
class MultilingualTextField(forms.CharField):
    """Custom field using marker format for multilingual text."""
    
    # Users input text with markers:
    # ==en==
    # English text
    # ==pt==
    # Portuguese text
    
    def to_python(self, value):
        """Convert marker format to JSON dict."""
        # Parses ==lang== markers and builds JSON dict
        # Plain text without markers → {"none": text}
    
    def prepare_value(self, value):
        """Convert JSON dict to marker format for display."""
        # Reverses conversion for editing
```

**QuestionForm**
```python
class QuestionForm(forms.ModelForm):
    """Form for creating/editing questions."""
    
    text = MultilingualTextField(
        widget=forms.Textarea,
        help_text="Use ==en==, ==pt== markers for languages"
    )
    
    class Meta:
        model = Question
        fields = ["title", "subject", "text"]
```

**ChoiceInlineFormSet**
```python
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=["text"],  # Order managed by position, not form field
    extra=0,
    can_delete=False,  # Handled via JavaScript
    min_num=2,
    validate_min=True,
)
```

### 7. Templates

**questions/question_list.html**
- Subject filter dropdown (auto-submits on change)
- Checkbox: "Include questions from sub-subjects" (auto-submits)
- Table with columns: Title (with text preview), Subject, Choices, Languages, Actions
- Clear filter button (no Apply button needed)
- Pagination

**questions/question_form.html**
- Title input field (first)
- Subject selector
- Question text textarea with marker format help text
- Inline choice formset with JavaScript controls:
  - Add choice button
  - Delete choice button (minimum 2 enforced)
  - Move up/down buttons
  - Dynamic correct answer badge on first choice
  - Automatic form field renumbering on reorder
- Save/Cancel buttons

**questions/question_preview.html**
- Title displayed prominently in card header
- Subject shown with link to filtered question list
- Card layout with language columns
- Each card shows one language version with **markdown rendering**
- Question text + all choices (markdown formatted)
- First choice highlighted in green as correct answer
- Fallback indicators: "Language Independent", "Using fallback"

**questions/question_confirm_delete.html**
- Warning about cascade deletion of choices
- Show question title and text
- Show choice count
- Confirm/Cancel

### 8. Markdown Support

Question and choice text supports markdown rendering:

**Template Tag:**
```python
@register.filter
def markdown(text):
    """Convert markdown to HTML."""
    return mark_safe(markdown_lib.markdown(
        text,
        extensions=['nl2br', 'fenced_code', 'tables', 'sane_lists']
    ))
```

**Features:**
- Line breaks preserved with `nl2br` extension
- Code blocks with syntax highlighting
- Tables for structured data
- Lists with proper formatting
- Safe HTML output

### 9. Subject Integration

Subjects now display question counts and link to filtered questions:

**Subject Model:**
```python
def get_question_count(self) -> int:
    """Return count of questions directly assigned to this subject."""
    return self.questions.count()
```

**Subject List View:**
- Each subject shows question count badge
- Badge is clickable link to filtered question list
- Count displayed for all hierarchy levels

### 10. Static Files Organization

**App-Specific JavaScript:**
- `apps/questions/static/questions/js/question_form.js` - Choice management
- `apps/questions/static/questions/js/question_list.js` - Auto-filter
- `apps/common/static/common/js/main.js` - Shared functionality

**Django Compressor:**
- All JS/CSS wrapped in `{% compress %}` tags
- Scripts loaded with `defer` attribute
- No `DOMContentLoaded` wrappers needed
- Files minified and concatenated in production

### 11. URLs

```
/questions/ - List all questions (with filters)
/questions/by-subject/<subject_uuid>/ - Questions for specific subject
/questions/create/ - Create new question
/questions/create/?subject=<uuid> - Create with pre-selected subject
/questions/<uuid>/ - Preview question
/questions/<uuid>/edit/ - Edit question
/questions/<uuid>/delete/ - Delete question
```

### 12. Admin Configuration

```python
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "choice_count", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["title", "text"]
    
    fieldsets = [
        ("Question Information", {
            "fields": ["title", "subject", "text"]
        }),
        ("Metadata", {
            "fields": ["id", "created_at", "updated_at"],
            "classes": ["collapse"]
        })
    ]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["get_text_preview", "question", "order"]
    list_filter = ["question__subject"]
```

### 13. Database Considerations

**Indexes:**
```python
class Question(UUIDModel):
    class Meta:
        indexes = [
            models.Index(fields=["subject", "-created_at"]),
            # GIN index for JSON field (PostgreSQL)
            # migrations will need raw SQL for this
        ]
```

**Migration Notes:**
- SQLite JSON support is basic, PostgreSQL is better
- Consider adding GIN index on JSON fields in production
- May need custom migration for JSON indexing

### 14. Testing Strategy

**Model Tests:**
- Question creation with valid/invalid JSON
- Choice creation and ordering
- Language fallback logic (all scenarios)
- Cascade deletion of choices
- Foreign key constraints

**View Tests:**
- List questions with/without sub-subject filter
- Create question with choices (valid/invalid)
- Edit question and choices
- Delete question
- Preview shows all languages correctly

**Form Tests:**
- JSON validation
- Minimum choice requirement
- Language key validation

**Integration Tests:**
- Create question → add choices → preview → edit → delete
- Subject filter with sub-subjects
- Multiple languages workflow

## Alternatives Considered

### Alternative 1: Separate Translation Model
```python
class QuestionTranslation(models.Model):
    question = ForeignKey(Question)
    language_code = CharField(max_length=10)
    text = TextField()
```

**Pros:** 
- More traditional Django approach
- Easier to query specific language
- Better for many languages (100+)

**Cons:** 
- More complex queries for fallback logic
- Additional table and joins
- More boilerplate code

**Decision:** Rejected for v1. JSONField is simpler and sufficient for typical use cases (2-5 languages). Can migrate later if needed.

### Alternative 2: django-modeltranslation
**Pros:** Established library, automatic admin integration  
**Cons:** Additional dependency, less flexible, harder to customize fallback  
**Decision:** Rejected - our fallback logic is custom, JSONField gives more control

### Alternative 3: Separate text field per language
**Pros:** Simple, no JSON parsing  
**Cons:** Inflexible, requires schema changes for new languages  
**Decision:** Rejected - doesn't scale with language additions

## Implementation Plan

### Phase 1: Models & Migrations
1. Create `apps/questions/` Django app
2. Implement Question model with JSONField
3. Implement Choice model with JSONField
4. Create multilingual text validator
5. Create and run migrations
6. Write model tests (including language fallback)

### Phase 2: Admin Interface
1. Register Question and Choice in admin
2. Configure list displays and filters
3. Test admin CRUD operations
4. Verify JSON editing in admin

### Phase 3: Forms & Views
1. Implement QuestionForm with language handling
2. Create ChoiceInlineFormSet
3. Implement QuestionListView with filters
4. Implement QuestionCreateView with inline choices
5. Implement QuestionUpdateView
6. Implement QuestionDeleteView
7. Implement QuestionPreviewView
8. Write view tests

### Phase 4: Templates & UI
1. Create question_list.html with subject filter
2. Create question_form.html with language tabs
3. Add JavaScript for dynamic choice addition
4. Add JavaScript for language tab management
5. Create question_preview.html with multi-language display
6. Create question_confirm_delete.html
7. Update subject detail to link to questions

### Phase 5: Integration & Polish
1. Add URL configuration
2. Update base navigation
3. Link subjects to questions
4. Run full test suite
5. Code review and cleanup
6. Update SYSTEM.md documentation

## Success Metrics

✅ **Achieved:**
- 27 tests passing with 91% model coverage
- Questions have mandatory title field
- Marker format (==lang==) for easy multilingual input
- Markdown rendering with line breaks, code blocks, tables
- Can create question with 2+ choices using custom JS controls
- Language fallback works correctly in all scenarios
- Auto-filter by subject with sub-subjects checkbox
- Preview displays all language versions with markdown
- Custom JavaScript choice management (add/delete/move)
- Admin interface shows title and searches both title and text
- Question counts integrated with subject list
- Django compressor with deferred script loading
- Code organized by app in static folders

## Timeline Estimate

- Phase 1 (Models): 1.5 hours
- Phase 2 (Admin): 0.5 hours
- Phase 3 (Forms/Views): 3 hours
- Phase 4 (Templates/UI): 2.5 hours
- Phase 5 (Integration): 1 hour

**Total:** ~8.5 hours

## Future Enhancements

Deferred to future iterations:
- Choice randomization for quiz/exam display
- Multiple correct answers support
- Variable substitution in question/choice text
- Question types (true/false, short answer, etc.)
- Rich text editor for question/choice text (currently markdown)
- Image/media attachments
- Question difficulty levels
- Question tags/categories beyond subjects
- Auto-translation suggestions
- Question import from various formats (Moodle XML, CSV, etc.)
- Question export to Moodle XML with variants
- Analytics and usage tracking
- Question versioning
