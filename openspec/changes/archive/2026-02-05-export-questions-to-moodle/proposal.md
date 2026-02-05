# Proposal: Export Questions to Moodle XML Format

## Why

### Problem Statement

Currently, Qoodle allows teachers to create exams with question pools and templates, but there's no way to actually deliver these exams to students. The exams exist only as specifications - teachers can't export them to Moodle for actual testing.

### User Need

Teachers need to:
1. **Export exam questions to Moodle XML format** for importing into their Moodle course
2. **Control grading behavior** by choosing between single-choice (traditional) and multi-choice (allow partial credit tracking)
3. **Use custom grading schemes** that allow Excel-based analysis of student answer patterns
4. **Generate multiple question variants** from each template using the variable substitution system
5. **Set default grades** for each question in the exam

### Context

This builds on three existing systems:
- **QuestionTemplate with Variables** - Templates can generate multiple variants through variable substitution
- **Exam Management** - Exams have ordered pools with templates and `number_of_versions` settings
- **Multilingual Questions** - Questions stored with `==lang==` markers in JSONField with fallback logic

The export system will transform these abstract specifications into concrete Moodle XML files that can be imported directly into Moodle quiz banks.

### Custom Grading Rationale

The proposed multi-choice grading scheme enables sophisticated answer pattern analysis:

**For 2-choice questions (correct: 90%, wrong: 10%):**
- Score 100% = correct + 1 wrong (student selected all)
- Score 90% = correct only (ideal answer)
- Score 10% = 1 wrong

**For 3-choice questions (correct: 80%, wrong: 10%):**
- Score 100% = correct + 2 wrong (student selected all)
- Score 90% = correct + 1 wrong
- Score 80% = correct only (ideal answer)
- Score 20% = 2 wrong
- Score 10% = 1 wrong

**For 4-choice questions (correct: 70%, wrong: 10%):**
- Score 100% = correct + 3 wrong (student selected all)
- Score 80% = correct + 1 wrong
- Score 70% = correct only (ideal answer)
- Score 30% = 3 wrong
- Score 20% = 2 wrong
- Score 10% = 1 wrong

**For 5-choice questions (correct: 60%, wrong: 10%):**
- Score 100% = correct + 4 wrong (student selected all)
- Score 90% = correct + 3 wrong
- Score 80% = correct + 2 wrong
- Score 70% = correct + 1 wrong
- Score 60% = correct only (ideal answer)
- Score 40% = 3 wrong
- Score 30% = 3 wrong
- Score 20% = 2 wrong
- Score 10% = 1 wrong

**For 6-choice questions (correct: 75%, wrong: 5%):**
- Score 100% = correct + 5 wrong
- Score 80% = correct + 1 wrong
- Score 75% = correct only (ideal answer)
- Score 25% = 5 wrong


Notes:

- Notice that for 6-choice, correct: 50%, wrong: 10% is not possible as we wouldn't be able to understand the different between 1 correct or 5 wrong.
- For other cases we can just throw an error saying multichoice is only valid between 2 and 6 choices.
- This should be easily extended to other cases by adding them in the code, we don't need to have any clever way to add these rules in the database or files (hardcoded is enough)

This allows teachers to use Excel formulas to analyze not just correctness but also student confidence and guessing patterns.

## What Changes

### Core Changes

**1. Add Question Grading Mode to Exam**

Add a field to the Exam model to specify export mode:
- `grading_mode` (CharField): "single" or "multi" (default: "single")

**2. Add Default Grade to QuestionPool**

Add a field to QuestionPool to specify point value:
- `default_grade` (DecimalField): Points for this question (default: 1.0)

**3. New Moodle XML Export System**

Create a new module `apps/exams/moodle_export.py` with:
- `generate_moodle_xml(exam, language)` - Main export function
- `calculate_fractions(num_choices, grading_mode)` - Grading scheme logic
- `substitute_variables(template_text, seed)` - Variable generation
- `format_html_for_moodle(markdown_text)` - Convert markdown to CDATA-wrapped HTML

**4. Export View and Download**

Add a new view `ExamMoodleExportView` at `/exams/<uuid:pk>/export/`:
- Form to select language (en, pt, etc.) and confirm export
- Generates XML file with all question variants
- Returns as downloadable `.xml` file
- Question tags: Q1, Q2, Q3... (pool position in exam, repeated for each variant)
- Question names: Q1, Q1, Q1... (pool position in exam, repeated for each variant)

### XML Structure

Each question in the export will have:
```xml
<question type="multichoice">
  <tags><tag><text>q{pool_order}</text></tag></tags>
  <name><text>Q{pool_order}</text></name>
  <defaultgrade>{pool.default_grade}</defaultgrade>
  <questiontext format="html">
    <text><![CDATA[<p>{rendered_question_text}</p>]]></text>
  </questiontext>
  <answer format="html" fraction="{calculated_fraction}">
    <text><![CDATA[<p>{rendered_choice_text}</p>]]></text>
  </answer>
  <!-- more answers -->
  <shuffleanswers>1</shuffleanswers>
  <single>{true|false}</single>
  <answernumbering>abc</answernumbering>
</question>
```

Notes:
- single should be true for singlechoice, and false for multichoice (for now, it will be the same for the complete exam, there are no exams with dual mode)
- the question type is always multichoice (it just means if it is a question where the user muset select and answer, the single atribbute controls if the student can select many choices)

### Fraction Calculation Logic

**Single Choice Mode:**
- Correct answer (order=0): `fraction="100"`
- Wrong answers: `fraction="-33.33333"`

**Multi Choice Mode (2 choices):**
- Correct answer (order=0): `fraction="90"`
- Wrong answers: `fraction="10"`

**Multi Choice Mode (3 choices):**
- Correct answer (order=0): `fraction="80"`
- Wrong answers: `fraction="10"`

**Multi Choice Mode (4 choices):**
- Correct answer (order=0): `fraction="70"`
- Wrong answers: `fraction="10"`

**Multi Choice Mode (5 choices):**
- Correct answer (order=0): `fraction="60"`
- Wrong answers: `fraction="10"`

**Multi Choice Mode (6 choices):**
- Correct answer (order=0): `fraction="75"`
- Wrong answers: `fraction="5"`

**Multi Choice Mode (other counts):**
- Throw error

## Capabilities

### New Capabilities

1. **moodle-xml-export** (NEW)
   - Export exam to Moodle XML format
   - Generate question variants using variable substitution
   - Apply single/multi choice grading schemes
   - Convert markdown to HTML with CDATA wrapping

2. **question-variant-generation** (NEW)
   - Generate N variants per template based on `number_of_versions`
   - Use seeded random generation for consistent results
   - Substitute variables in both question text and choices

3. **grading-mode-selection** (NEW)
   - Teachers select single vs multi choice at exam level
   - Custom fraction calculation for answer pattern tracking

### Modified Capabilities

1. **exam-management** (MODIFIED)
   - Add `grading_mode` field to Exam model
   - Add "Export to Moodle" button on exam detail page

2. **question-pool-management** (MODIFIED)
   - Add `default_grade` field to QuestionPool model
   - Display/edit default grade in pool management UI

## Impact

### Database Changes

**Migration 1: Add grading_mode to Exam**
```python
migrations.AddField(
    model_name='exam',
    name='grading_mode',
    field=models.CharField(
        max_length=10,
        choices=[('single', 'Single Choice'), ('multi', 'Multiple Choice')],
        default='single'
    )
)
```

**Migration 2: Add default_grade to QuestionPool**
```python
migrations.AddField(
    model_name='questionpool',
    name='default_grade',
    field=models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.1)]
    )
)
```

### Dependencies

**No new dependencies required** - using Python standard library:
- `xml.etree.ElementTree` - XML generation
- `xml.dom.minidom` - Pretty-printing
- Built-in markdown library (already in project)

### UI Changes

1. **Exam Form (Create/Edit):**
   - Add "Grading Mode" radio buttons (Single Choice / Multiple Choice)

2. **Exam Detail Page:**
   - Add "Export to Moodle" button in header
   - Each pool shows default grade field (inline editable)

3. **Export Form (New Page):**
   - Language selection dropdown (en, pt, fr, etc.)
   - Preview of question count (pools × variants)
   - "Download XML" button

### Files to Create

- `apps/exams/moodle_export.py` - Export logic (~200 lines)
- `apps/exams/templates/exams/exam_export.html` - Export form (~50 lines)
- `apps/exams/tests_moodle_export.py` - Export tests (~150 lines)

### Files to Modify

- `apps/exams/models.py` - Add fields to Exam and QuestionPool
- `apps/exams/forms.py` - Update ExamForm
- `apps/exams/views.py` - Add ExamMoodleExportView
- `apps/exams/urls.py` - Add export URL pattern
- `apps/exams/templates/exams/exam_detail.html` - Add export button
- `apps/exams/templates/exams/exam_form.html` - Add grading mode field

### Risks

1. **Variable Substitution Complexity**
   - Risk: Variable generation might fail or produce invalid content
   - Mitigation: Validate templates before export, show preview
   - Fallback: Export without substitution if validation fails

2. **Language Fallback Edge Cases**
   - Risk: Some questions might not have content in selected language
   - Mitigation: Use existing fallback logic (==en== → first available)
   - Test with mixed-language question sets

3. **XML Escaping**
   - Risk: Special characters in markdown might break XML
   - Mitigation: Use CDATA sections for all text content
   - Test with HTML entities, code blocks, quotes

4. **Large Exam Performance**
   - Risk: Exam with 50 pools × 10 variants = 500 questions might be slow
   - Mitigation: Stream XML generation, add progress indicator
   - Limit: Warn if total questions > 200

5. **Moodle Compatibility**
   - Risk: Different Moodle versions might have XML variations
   - Mitigation: Target Moodle 4.x XML schema (most common)
   - Documentation: Note tested Moodle versions

## Verification Plan

### Management Command Test

Create a management command for testing:
```bash
poetry run python manage.py export_exam_to_moodle <exam_id> --language=en --output=exam.xml
```

This command will:
1. Load exam by ID
2. Generate all question variants
3. Write XML to file
4. Print statistics (pools, variants, total questions)

### Validation Steps

1. **Create test exam:**
   - 3 pools with 2 templates each
   - 3 versions per template
   - Total: 18 questions (3 × 2 × 3)

2. **Export and validate:**
   - Run export command
   - Validate XML structure with `xmllint`
   - Import into Moodle test instance
   - Verify question rendering and grading

3. **Test grading schemes:**
   - Single choice: Verify 100/-33.33 fractions
   - Multi choice (4): Verify 70/10 fractions
   - Multi choice (6): Verify 75/5 fractions

4. **Test variable substitution:**
   - Template with `{{variable}}` markers
   - Verify each variant has different values
   - Verify deterministic generation (same seed = same output)

## Out of Scope (Future Work)

The following are explicitly NOT included in this change:

- ❌ Import Moodle XML back into Qoodle
- ❌ Question bank export (only exams, although technically we are exporting a question bank in terms of moodle)
- ❌ GIFT format export
- ❌ Advanced question types (matching, essay, numerical)
- ❌ Question images or media attachments
- ❌ Category/taxonomy mapping
- ❌ Custom fraction schemes (user-defined percentages)
- ❌ Batch export (multiple exams at once)

These will be addressed in future changes after validating the core export workflow.

## Success Criteria

This change is successful when:

1. ✅ Teachers can select grading mode (single/multi) when creating exams
2. ✅ Teachers can set default grade for each pool
3. ✅ Export view generates valid Moodle XML file
4. ✅ Single choice uses 100/-33.33 fractions
5. ✅ Multi choice uses 70/10 (4 choices) or 75/5 (6 choices) fractions (or toher modes from 2 to 6 choices)
5. ✅ Multi choice with more than 6 choices throws error (with alert to user)
6. ✅ Each template generates N **different** variants based on `number_of_versions`
6. ✅ If unable to generate all variants, throws error (with alert to user)
7. ✅ Questions are tagged Q1, Q2, Q3... matching pool order (repeated for each variant and template in the pool)
8. ✅ Variable substitution works in question text and choices
9. ✅ Markdown is converted to HTML and wrapped in CDATA
10. ✅ Exported XML imports successfully into Moodle 4.x
11. ✅ Test coverage >80% for export module
12. ✅ Language fallback works correctly in export

## Timeline Estimate

- **Phase 1 (Models):** 1 day - Add fields, migrations
- **Phase 2 (Export Logic):** 2-3 days - XML generation, variable substitution
- **Phase 3 (Views/UI):** 1-2 days - Export form, download view
- **Phase 4 (Testing):** 1-2 days - Unit tests, Moodle validation
- **Phase 5 (Polish):** 1 day - Error handling, documentation

**Total:** ~6-9 days for complete implementation and validation
