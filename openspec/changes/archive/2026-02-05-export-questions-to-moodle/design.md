# Design: Export Questions to Moodle XML Format

## Context

This change enables Qoodle exams to be exported to Moodle XML format, allowing teachers to import their parametric, multilingual question banks directly into Moodle quizzes. The system builds on three existing capabilities:

1. **QuestionTemplate with Variables** - Templates define variable placeholders that generate multiple variants
2. **Exam Management** - Exams organize QuestionPools with templates and version settings  
3. **Multilingual Questions** - Questions use `==lang==` markers stored in JSONFields

The export process transforms these abstract specifications into concrete Moodle XML files with:
- Multiple question variants generated via seeded random substitution
- Language-specific content extraction with fallback logic
- Custom grading fractions for answer pattern analysis
- Markdown-to-HTML conversion with CDATA wrapping

**Key Architectural Constraint:** Python stdlib only (xml.etree.ElementTree, xml.dom.minidom). No external dependencies.

## Goals / Non-Goals

**Goals:**

1. **Enable Moodle Import:** Generate valid Moodle 4.x XML that imports cleanly into quiz banks
2. **Support Custom Grading:** Implement 5 hardcoded fraction schemes (2-6 choices) for Excel analysis
3. **Deterministic Variants:** Use `hash(template.id_version)` seed for reproducible question generation
4. **Multilingual Export:** Extract language-specific content with fallback to default language
5. **Preserve Formatting:** Convert markdown to HTML while escaping special characters via CDATA
6. **Simple UI:** Single export button on exam detail with language dropdown

**Non-Goals:**

- Dynamic/configurable grading schemes (hardcoded 5 schemes is sufficient)
- Multi-language exports (one language per export)
- Bulk export of multiple exams
- Automatic Moodle upload (download XML file only)
- Question difficulty/taxonomy metadata
- Image attachments or embedded media

## Decisions

### 1. Hardcoded Fraction Schemes (2-6 Choices)

**Decision:** Calculate single-choice fractions dynamically using formula `-100/(n-1)`, implement multi-choice as 5 hardcoded schemes.

**Rationale:**
- Single-choice penalty is formulaic: wrong_fraction = -100 / (num_choices - 1)
- Multi-choice schemes are not formulaic (6-choice uses 75/5, not 50/10)
- Single-choice supports any number of choices ≥2
- Multi-choice limited to 2-6 choices for pattern tracking
- Simpler to test and maintain than dynamic configuration

**Implementation:**
```python
def calculate_fractions(num_choices: int, grading_mode: str) -> dict[str, Decimal]:
    """Calculate answer fractions for Moodle XML export."""
    if grading_mode == 'single':
        # Formula: wrong penalty = -100 / (num_choices - 1)
        # Examples: 2 choices=-100%, 3=-50%, 4=-33.33%, 5=-25%, 6=-20%
        if num_choices < 2:
            raise ValueError(f"Questions must have at least 2 choices, got {num_choices}")
        wrong_fraction = -100.0 / (num_choices - 1)
        return {
            'correct': Decimal('100.0'),
            'wrong': Decimal(str(round(wrong_fraction, 5)))
        }
    
    # Multi-choice schemes (hardcoded for pattern tracking)
    schemes = {
        2: {'correct': Decimal('90.0'), 'wrong': Decimal('10.0')},
        3: {'correct': Decimal('80.0'), 'wrong': Decimal('10.0')},
        4: {'correct': Decimal('70.0'), 'wrong': Decimal('10.0')},
        5: {'correct': Decimal('60.0'), 'wrong': Decimal('10.0')},
        6: {'correct': Decimal('75.0'), 'wrong': Decimal('5.0')},
    }
    
    if num_choices not in schemes:
        raise ValueError(
            f"Multi-choice grading only supports 2-6 choices, got {num_choices}"
        )
    
    return schemes[num_choices]
```

**Alternatives considered:**
- **Database storage:** Rejected - adds complexity without benefit (schemes won't change)
- **YAML/JSON config:** Rejected - makes testing harder, no dynamic loading needed
- **Algorithmic calculation:** Rejected - schemes aren't formulaic (6-choice uses 75/5, not 50/10)

### 2. Seeded Random for Deterministic Variant Generation

**Decision:** Use `hash(f"{template.id}_{version_number}")` as random seed for variable generation.

**Rationale:**
- **Reproducibility:** Same template + version always generates same question
- **No Storage:** Don't need to persist generated variants in database
- **Uniqueness:** Different versions get different seeds → different values
- **Cross-export Consistency:** Re-exporting an exam produces identical XML

**Implementation:**
```python
import random
import hashlib

def generate_variant(
    template: QuestionTemplate,
    version_number: int,
    language: str
) -> dict[str, str]:
    """Generate deterministic question variant."""
    # Create seed from template ID and version
    seed_string = f"{template.id}_{version_number}"
    seed = int(hashlib.md5(seed_string.encode()).hexdigest(), 16) % (2**32)
    
    rng = random.Random(seed)
    
    # Generate variable values
    values = {}
    for var_name, config in template.variables.items():
        if config['type'] == 'integer':
            values[var_name] = rng.randint(config['min'], config['max'])
        elif config['type'] == 'float':
            val = rng.uniform(config['min'], config['max'])
            values[var_name] = round(val, config.get('decimals', 2))
        elif config['type'] == 'choice':
            values[var_name] = rng.choice(config['options'])
    
    # Substitute variables in text
    text = extract_language_text(template.text, language)
    for var, val in values.items():
        text = text.replace(f"{{{{{var}}}}}", str(val))
    
    return {'text': text, 'values': values}
```

**Alternatives considered:**
- **Store variants in DB:** Rejected - wastes storage, complicates migrations
- **UUID-based seed:** Rejected - hash of UUID+version is less intuitive
- **Sequential seed (0, 1, 2...):** Rejected - same seed across templates causes value correlation

### 3. Uniqueness Validation with 50-Attempt Retry

**Decision:** After generating all variants, check for duplicate question text. If duplicates exist, regenerate with incremented seed offset (up to 50 attempts).

**Rationale:**
- **Prevent identical questions:** Variable ranges may be narrow, causing collisions
- **Graceful failure:** Error message better than silent duplicates
- **Bounded complexity:** 50 attempts sufficient for reasonable variable ranges

**Implementation:**
```python
def generate_all_variants(
    template: QuestionTemplate,
    num_versions: int,
    language: str
) -> list[dict]:
    """Generate unique question variants with collision detection."""
    max_attempts = 50
    
    for attempt in range(max_attempts):
        variants = []
        for version in range(num_versions):
            # Add attempt offset to seed for retry attempts
            effective_seed = f"{template.id}_{version}_{attempt}"
            variant = generate_variant_with_seed(template, effective_seed, language)
            variants.append(variant)
        
        # Check uniqueness
        texts = [v['text'] for v in variants]
        if len(texts) == len(set(texts)):  # All unique
            return variants
    
    # Failed after max attempts
    raise ValueError(
        f"Could not generate {num_versions} unique variants for template {template.id} "
        f"after {max_attempts} attempts. Consider widening variable ranges."
    )
```

**Alternatives considered:**
- **No validation:** Rejected - duplicate questions confuse students
- **Infinite retry:** Rejected - could loop forever on impossible constraints
- **100+ attempts:** Rejected - 50 sufficient, higher suggests design problem

### 4. XML Generation with stdlib (ElementTree + minidom)

**Decision:** Use `xml.etree.ElementTree` for structure building and `xml.dom.minidom` for pretty-printing.

**Rationale:**
- **No Dependencies:** Part of Python stdlib (aligns with project constraint)
- **Moodle Compatibility:** Supports CDATA sections needed for HTML content
- **Type Safety:** Can use type hints with standard library types
- **Testing:** Easy to test with string comparison

**Implementation:**
```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_moodle_xml(exam: Exam, language: str) -> str:
    """Generate Moodle XML for exam."""
    quiz = ET.Element('quiz')
    
    question_number = 1
    for pool in exam.pools.all().order_by('order'):
        for template in pool.templates.all():
            num_versions = template.number_of_versions or 1
            variants = generate_all_variants(template, num_versions, language)
            
            for variant in variants:
                question = ET.SubElement(quiz, 'question', type='multichoice')
                
                # Name and tags
                ET.SubElement(question, 'name').append(
                    ET.Element('text', text=f"Q{question_number}")
                )
                ET.SubElement(question, 'tags').append(
                    ET.Element('tag', text=f"<text>q{question_number}</text>")
                )
                
                # Question text (CDATA-wrapped HTML)
                html = format_html_for_moodle(variant['text'])
                questiontext = ET.SubElement(question, 'questiontext', format='html')
                text_elem = ET.SubElement(questiontext, 'text')
                text_elem.text = f"<![CDATA[{html}]]>"
                
                # Answers with fractions
                choices = get_choices_for_variant(template, variant, language)
                fractions = calculate_fractions(len(choices), exam.grading_mode)
                
                for choice in choices:
                    fraction = fractions['correct'] if choice['is_correct'] else fractions['wrong']
                    answer = ET.SubElement(question, 'answer', fraction=str(fraction))
                    
                    html_choice = format_html_for_moodle(choice['text'])
                    text_elem = ET.SubElement(answer, 'text')
                    text_elem.text = f"<![CDATA[{html_choice}]]>"
                                # Single attribute (true for single-choice, false for multi-choice)
                single_value = 'true' if exam.grading_mode == 'single' else 'false'
                ET.SubElement(question, 'single').text = single_value
                                # Default grade
                ET.SubElement(question, 'defaultgrade').text = str(pool.default_grade)
                
                question_number += 1
    
    # Pretty-print XML
    xml_string = ET.tostring(quiz, encoding='unicode')
    dom = minidom.parseString(xml_string)
    return dom.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')
```

**Alternatives considered:**
- **lxml:** Rejected - external dependency, overkill for this use case
- **Manual string building:** Rejected - error-prone, hard to maintain
- **jinja2 template:** Rejected - adds dependency, harder to test structure

### 5. Markdown to HTML with CDATA Wrapping

**Decision:** Use Python markdown library (already in project) with CDATA wrapping for Moodle compatibility.

**Rationale:**
- **Preserve Formatting:** Questions often include code blocks, lists, emphasis
- **CDATA Escaping:** Moodle requires CDATA sections for HTML content with `<>` chars
- **Existing Dependency:** `markdown` already used for question rendering

**Implementation:**
```python
import markdown

def format_html_for_moodle(markdown_text: str) -> str:
    """Convert markdown to HTML suitable for Moodle CDATA sections."""
    md = markdown.Markdown(extensions=[
        'nl2br',  # Newlines → <br>
        'fenced_code',  # ``` code blocks
        'tables',
        'sane_lists'
    ])
    
    html = md.convert(markdown_text)
    
    # No need to escape - CDATA handles special chars
    # But we must NOT include ]]> in content (would break CDATA)
    if ']]>' in html:
        html = html.replace(']]>', ']]&gt;')
    
    return html
```

**Alternatives considered:**
- **Plain text export:** Rejected - loses formatting valuable for code examples
- **Custom HTML escaping:** Rejected - CDATA handles this better
- **Bleach sanitization:** Rejected - Moodle handles sanitization on import

### 6. Single Export View with Language Dropdown

**Decision:** Add export functionality as POST form on exam detail page, not separate page.

**Rationale:**
- **Contextual Action:** Export belongs to exam detail (not global navigation)
- **Single Parameter:** Only language selection needed (grading mode already on exam)
- **RESTful:** POST returns file download response

**URL Pattern:**
```python
path('exams/<uuid:pk>/export/', ExamExportView.as_view(), name='exams:export')
```

**View Implementation:**
```python
class ExamExportView(View):
    """Export exam to Moodle XML format."""
    
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        language = request.POST.get('language', 'en')
        
        try:
            xml_content = generate_moodle_xml(exam, language)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('exams:detail', pk=exam.pk)
        
        # Return XML file download
        response = HttpResponse(xml_content, content_type='application/xml')
        filename = f"{exam.title.replace(' ', '_')}_{language}.xml"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
```

**UI (exam_detail.html):**
```html
<form method="post" action="{% url 'exams:export' exam.pk %}" class="d-inline">
  {% csrf_token %}
  <div class="input-group" style="width: 300px;">
    <select name="language" class="form-select">
      <option value="en">English</option>
      <option value="pt">Português</option>
    </select>
    <button type="submit" class="btn btn-success">
      <i class="fas fa-download"></i> Export to Moodle
    </button>
  </div>
</form>
```

**Alternatives considered:**
- **Separate export page:** Rejected - unnecessary navigation step
- **GET request:** Rejected - not idempotent (generates file)
- **Background job:** Rejected - export is fast enough for synchronous response

### 7. Database Schema Changes

**Decision:** Add two new fields via single migration:
1. `Exam.grading_mode` (CharField with choices, default='single')
2. `QuestionPool.default_grade` (DecimalField, default=1.0)

**Migration Strategy:**
```python
# Migration: 0005_exam_grading_mode_pool_grade.py

class Migration(migrations.Migration):
    dependencies = [
        ('exams', '0004_previous_migration'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='exam',
            name='grading_mode',
            field=models.CharField(
                max_length=10,
                choices=[('single', 'Single Choice'), ('multi', 'Multiple Choice')],
                default='single',
                help_text='Single: one correct answer. Multi: partial credit tracking.'
            ),
        ),
        migrations.AddField(
            model_name='questionpool',
            name='default_grade',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal('1.0'),
                validators=[MinValueValidator(Decimal('0.1'))],
                help_text='Point value for questions in this pool'
            ),
        ),
    ]
```

**Rationale:**
- **Backwards Compatible:** Default values ensure existing exams work unchanged
- **Single Migration:** Both fields related to same feature, ship together
- **Validation:** MinValueValidator prevents 0-point questions

### 8. Module Organization

**Decision:** Create standalone `apps/exams/moodle_export.py` module for export logic.

**File Structure:**
```
apps/exams/
├── models.py (Exam, QuestionPool models)
├── views.py (ExamExportView)
├── forms.py (ExamForm with grading_mode)
├── moodle_export.py (NEW - export logic)
│   ├── generate_moodle_xml()
│   ├── calculate_fractions()
│   ├── generate_variant()
│   ├── generate_all_variants()
│   ├── format_html_for_moodle()
│   └── extract_language_text()
└── tests.py (100+ tests including export scenarios)
```

**Rationale:**
- **Separation of Concerns:** Export logic distinct from views/models
- **Testability:** Pure functions easier to unit test
- **Reusability:** Could support other formats (GIFT, QTI) in future
- **Django Convention:** Keep views.py focused on HTTP handling

**Alternatives considered:**
- **utils.py:** Rejected - too generic, export is domain logic
- **exporters/ package:** Rejected - overkill for single format
- **In views.py:** Rejected - violates SRP, makes testing harder

### 9. Template Organization

**Decision:** Modify existing templates rather than create new ones.

**Templates Modified:**
1. `apps/exams/templates/exams/exam_detail.html` - Add export form
2. `apps/exams/templates/exams/exam_form.html` - Add grading_mode radio buttons

**Rationale:**
- **Contextual Actions:** Export belongs on detail page
- **Form Integration:** Grading mode is exam creation/edit concern
- **No New Pages:** Minimize navigation complexity

## Risks / Trade-offs

### Risk 1: Variable Range Too Narrow → Duplicate Variants

**Problem:** If template defines `{{number}}` with range [1, 2] and requests 10 versions, uniqueness validation will fail after 50 attempts.

**Mitigation:**
- Clear error message with actionable advice: "Consider widening variable ranges"
- Document recommended ranges in UI help text (e.g., "min 3x versions")
- Test coverage for collision scenarios

**Trade-off:** Could auto-expand ranges, but that would surprise users with unexpected values.

### Risk 2: CDATA Injection with `]]>` in Content

**Problem:** If markdown content includes `]]>`, it breaks CDATA section parsing.

**Mitigation:**
- Escape `]]>` → `]]&gt;` in `format_html_for_moodle()`
- Unlikely in practice (rare character sequence)

**Trade-off:** Technically possible but extremely rare edge case.

### Risk 3: Hardcoded Schemes Limit Future Flexibility

**Problem:** Only supports 2-6 choice questions with fixed fractions.

**Mitigation:**
- Error message for >6 choices suggests single-choice mode as fallback
- Schemes are sufficient for documented Excel analysis use case
- Future: Could add database/config storage if needed (not now)

**Trade-off:** Simplicity and testability now vs. theoretical future flexibility.

### Risk 4: Seed Collision Across Templates

**Problem:** `hash(template.id_version)` could theoretically collide for different templates (same hash).

**Mitigation:**
- UUID makes collisions astronomically unlikely (2^122 space)
- Even if collision occurs, only affects value correlation (not correctness)
- Each template has independent variable config

**Trade-off:** Acceptable risk given UUID entropy.

### Risk 5: Large Exams Cause Slow Exports

**Problem:** Exam with 100 pools × 10 versions × 6 choices = 6,000 XML elements, may take >2s to generate.

**Mitigation:**
- Synchronous response acceptable for <5s generation time
- Typical exams: 10-30 questions, well under threshold
- Future: Add Celery background task if needed

**Trade-off:** Simplicity now (no async infrastructure) vs. theoretical scale limit.

### Trade-off 1: Single Language Per Export

**Decision:** Require one language selection per export.

**Rationale:**
- Moodle quizzes are language-specific
- Multi-language export would require complex question naming scheme
- Teachers typically create separate quizzes per language

**Trade-off:** Must export twice for bilingual courses, but cleaner UX.

### Trade-off 2: Download Only (No Auto-Upload)

**Decision:** Return XML file download, don't POST to Moodle API.

**Rationale:**
- Moodle API authentication complex (OAuth, tokens)
- Import workflow well-understood by teachers
- No additional dependencies needed

**Trade-off:** Manual import step, but familiar workflow.

### Trade-off 3: No Image/Media Support

**Decision:** Export markdown → HTML without embedded images.

**Rationale:**
- Moodle XML supports images via base64 encoding, but complex
- Current questions are text/code-focused
- Image upload workflow not yet implemented in Qoodle

**Trade-off:** Can't export questions with images (future enhancement).
