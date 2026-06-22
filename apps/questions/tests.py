"""Tests for the questions app."""

import json
import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from django.urls import reverse

from apps.questions.models import Choice, QuestionTemplate, TemplateState, validate_multilingual_text
from apps.subjects.models import Subject


class ValidateMultilingualTextTests(TestCase):
    """Test cases for the validate_multilingual_text validator."""

    def test_valid_multilingual_text(self):
        """Test validation passes for valid multilingual text."""
        valid_texts = [
            {"none": "What is 4 + 5?"},
            {"en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"},
            {"none": "Text", "en": "Text", "pt": "Texto", "es": "Texto"},
        ]
        for text in valid_texts:
            validate_multilingual_text(text)  # Should not raise

    def test_invalid_not_dict(self):
        """Test validation fails for non-dictionary."""
        with self.assertRaises(ValidationError):
            validate_multilingual_text("not a dict")

    def test_invalid_empty_dict(self):
        """Test validation fails for empty dictionary."""
        with self.assertRaises(ValidationError):
            validate_multilingual_text({})

    def test_invalid_empty_string_value(self):
        """Test validation fails for empty string value."""
        with self.assertRaises(ValidationError):
            validate_multilingual_text({"en": ""})

    def test_invalid_whitespace_only(self):
        """Test validation fails for whitespace-only value."""
        with self.assertRaises(ValidationError):
            validate_multilingual_text({"en": "   "})

    def test_invalid_non_string_value(self):
        """Test validation fails for non-string value."""
        with self.assertRaises(ValidationError):
            validate_multilingual_text({"en": 123})


class QuestionModelTests(TestCase):
    """Test cases for the Question model."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_question_creation(self):
        """Test creating a basic question."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Addition Question", text={"none": "What is 4 + 5?"}
        )
        self.assertIsInstance(question.id, uuid.UUID)
        self.assertEqual(question.subject, self.subject)
        self.assertEqual(question.title, "Addition Question")
        self.assertEqual(question.text, {"none": "What is 4 + 5?"})
        self.assertIsNotNone(question.created_at)

    def test_question_str_representation(self):
        """Test string representation of question."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Test Question", text={"en": "What is the answer?"}
        )
        self.assertEqual(str(question), "Test Question")

    def test_get_text_specific_language(self):
        """Test retrieving text in specific language."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"},
        )
        self.assertEqual(question.get_text("en"), "What is 4 + 5?")
        self.assertEqual(question.get_text("pt"), "Quanto é 4 + 5?")

    def test_get_text_fallback_to_none(self):
        """Test fallback to language-independent text."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "4 + 5 = ?", "en": "What is 4 + 5?"},
        )
        # Request non-existent language, should fallback to "none"
        self.assertEqual(question.get_text("fr"), "4 + 5 = ?")

    def test_get_text_fallback_to_any_language(self):
        """Test fallback to any available language."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, text={"pt": "Quanto é 4 + 5?", "es": "¿Cuánto es 4 + 5?"}
        )
        # No "none" key, should fallback to first alphabetically
        result = question.get_text("fr")
        self.assertIn(result, ["Quanto é 4 + 5?", "¿Cuánto es 4 + 5?"])

    def test_get_text_no_language_specified(self):
        """Test getting text with no language specified."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "4 + 5 = ?", "en": "What is 4 + 5?"},
        )
        # Should return "none" when no language specified
        self.assertEqual(question.get_text(), "4 + 5 = ?")

    def test_get_text_no_none_key(self):
        """Test getting text with no language specified and no none key."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, text={"en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"}
        )
        # Should fallback to first alphabetically
        self.assertEqual(question.get_text(), "What is 4 + 5?")

    def test_available_languages(self):
        """Test retrieving available languages."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Text", "en": "English", "pt": "Portuguese"},
        )
        languages = question.available_languages()
        self.assertEqual(languages, {"none", "en", "pt"})

    def test_get_all_texts(self):
        """Test retrieving all text versions."""
        text_dict = {"none": "Text", "en": "English"}
        question = QuestionTemplate.objects.create(subject=self.subject, text=text_dict)
        self.assertEqual(question.get_all_texts(), text_dict)

    def test_choice_count(self):
        """Test choice count property."""
        question = QuestionTemplate.objects.create(subject=self.subject, text={"none": "Question?"})
        self.assertEqual(question.choice_count, 0)

        Choice.objects.create(template=question, text={"none": "Choice 1"}, order=0)
        Choice.objects.create(template=question, text={"none": "Choice 2"}, order=1)
        self.assertEqual(question.choice_count, 2)

    def test_correct_choice_property(self):
        """Test correct_choice property returns first choice."""
        question = QuestionTemplate.objects.create(subject=self.subject, text={"none": "Question?"})
        correct = Choice.objects.create(template=question, text={"none": "Correct"}, order=0)
        Choice.objects.create(template=question, text={"none": "Wrong"}, order=1)

        self.assertEqual(question.correct_choice, correct)

    def test_question_subject_protect(self):
        """Test that deleting subject is protected if it has questions."""
        question = QuestionTemplate.objects.create(subject=self.subject, text={"none": "Question?"})
        # Attempting to delete subject should raise ProtectedError
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.subject.delete()


class TagListTests(TestCase):
    """Test cases for the tag_list() method on QuestionTemplate."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_tag_list_empty_string(self):
        """Test tag_list returns empty list for empty tags."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="No Tags", text={"none": "Question?"}, tags=""
        )
        self.assertEqual(question.tag_list(), [])

    def test_tag_list_single_tag(self):
        """Test tag_list with a single tag."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="One Tag", text={"none": "Question?"}, tags="easy"
        )
        self.assertEqual(question.tag_list(), ["easy"])

    def test_tag_list_multiple_tags(self):
        """Test tag_list with multiple comma-separated tags."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Multiple Tags",
            text={"none": "Question?"},
            tags="easy, exam-2024, review",
        )
        self.assertEqual(question.tag_list(), ["easy", "exam-2024", "review"])

    def test_tag_list_strips_whitespace(self):
        """Test tag_list strips whitespace from tags."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Whitespace Tags",
            text={"none": "Question?"},
            tags="  easy ,  exam-2024 , review ",
        )
        self.assertEqual(question.tag_list(), ["easy", "exam-2024", "review"])

    def test_tag_list_filters_empty_entries(self):
        """Test tag_list filters out empty entries from consecutive commas."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Empty Entries",
            text={"none": "Question?"},
            tags="easy, , hard",
        )
        self.assertEqual(question.tag_list(), ["easy", "hard"])


class TemplateStateTests(TestCase):
    """Test cases for the state field on QuestionTemplate."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_default_state_is_draft(self):
        """Test new templates default to draft state."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Test", text={"none": "Question?"}
        )
        self.assertEqual(question.state, TemplateState.DRAFT)

    def test_state_can_be_set_to_reviewed(self):
        """Test state can be set to reviewed."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Test", text={"none": "Question?"}, state=TemplateState.REVIEWED
        )
        self.assertEqual(question.state, "reviewed")
        self.assertEqual(question.get_state_display(), "Reviewed")

    def test_state_can_be_set_to_completed(self):
        """Test state can be set to completed."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Test", text={"none": "Question?"}, state=TemplateState.COMPLETED
        )
        self.assertEqual(question.state, "completed")


class TemplateStateFilterTests(TestCase):
    """Test cases for filtering templates by state in list view."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")
        self.draft = QuestionTemplate.objects.create(
            subject=self.subject, title="Draft Q", text={"none": "Q?"}, state=TemplateState.DRAFT
        )
        self.reviewed = QuestionTemplate.objects.create(
            subject=self.subject, title="Reviewed Q", text={"none": "Q?"}, state=TemplateState.REVIEWED
        )
        self.completed = QuestionTemplate.objects.create(
            subject=self.subject, title="Completed Q", text={"none": "Q?"}, state=TemplateState.COMPLETED
        )

    def test_no_state_filter_shows_all(self):
        """Test that no state filter shows all templates."""
        response = self.client.get(reverse("questions:list"))
        questions = response.context["questions"]
        self.assertEqual(len(questions), 3)

    def test_filter_by_reviewed(self):
        """Test filtering by reviewed state."""
        response = self.client.get(reverse("questions:list") + "?state=reviewed")
        questions = response.context["questions"]
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].state, "reviewed")

    def test_filter_by_draft(self):
        """Test filtering by draft state."""
        response = self.client.get(reverse("questions:list") + "?state=draft")
        questions = response.context["questions"]
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].state, "draft")

    def test_selected_state_in_context(self):
        """Test that selected_state is passed to template context."""
        response = self.client.get(reverse("questions:list") + "?state=reviewed")
        self.assertEqual(response.context["selected_state"], "reviewed")


class QuestionListToggleTests(TestCase):
    """Test question text rendering for the template-list global toggle."""

    def setUp(self):
        """Create a multilingual template with Markdown and choices."""
        self.subject = Subject.objects.create(name="Mathematics")
        self.question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Addition",
            text={
                "none": "Calculate **{{a}} + {{b}}**.",
                "pt": "Calcule **{{a}} + {{b}}**.",
            },
        )
        Choice.objects.create(
            template=self.question,
            text={"none": "SECRET CORRECT CHOICE"},
            order=0,
        )
        Choice.objects.create(
            template=self.question,
            text={"none": "SECRET WRONG CHOICE"},
            order=1,
        )

    def test_list_has_one_global_toggle_and_hidden_question_row(self):
        """Test the list renders one hidden-by-default global toggle target."""
        response = self.client.get(reverse("questions:list"))

        self.assertContains(response, 'id="toggleQuestionTextBtn"', count=1)
        self.assertContains(response, "Show Questions", count=1)
        self.assertContains(
            response,
            'id="toggleQuestionTextBtn"\n                                aria-expanded="false"',
            count=1,
        )
        self.assertContains(response, 'class="question-text-row d-none"', count=1)

    def test_list_uses_model_fallback_and_preserves_variables(self):
        """Test display text uses fallback without generating variables."""
        response = self.client.get(reverse("questions:list"))
        listed_question = response.context["questions"][0]

        self.assertEqual(
            listed_question.display_question_text,
            "Calculate **{{a}} + {{b}}**.",
        )
        self.assertContains(response, "{{a}} + {{b}}")

    def test_list_renders_question_markdown_without_choices(self):
        """Test expanded content contains rendered question text only."""
        response = self.client.get(reverse("questions:list"))

        self.assertContains(response, "<strong>{{a}} + {{b}}</strong>", html=True)
        self.assertNotContains(response, "SECRET CORRECT CHOICE")
        self.assertNotContains(response, "SECRET WRONG CHOICE")

    def test_list_falls_back_to_first_available_language(self):
        """Test templates without none text use first language alphabetically."""
        self.question.text = {
            "pt": "Pergunta em português",
            "en": "English question",
        }
        self.question.save()

        response = self.client.get(reverse("questions:list"))
        listed_question = response.context["questions"][0]

        self.assertEqual(listed_question.display_question_text, "English question")
        self.assertContains(response, "English question")
        self.assertNotContains(response, "Pergunta em português")

    def test_empty_list_has_no_question_toggle(self):
        """Test an empty list does not render the global toggle."""
        self.question.delete()

        response = self.client.get(reverse("questions:list"))

        self.assertNotContains(response, 'id="toggleQuestionTextBtn"')


class ChoiceModelTests(TestCase):
    """Test cases for the Choice model."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")
        self.template = QuestionTemplate.objects.create(
            subject=self.subject, text={"none": "What is 4 + 5?"}
        )

    def test_choice_creation(self):
        """Test creating a basic choice."""
        choice = Choice.objects.create(template=self.template, text={"none": "9"}, order=0)
        self.assertIsInstance(choice.id, uuid.UUID)
        self.assertEqual(choice.template, self.template)
        self.assertEqual(choice.text, {"none": "9"})
        self.assertEqual(choice.order, 0)

    def test_choice_str_representation(self):
        """Test string representation of choice."""
        choice = Choice.objects.create(template=self.template, text={"en": "Nine"}, order=0)
        self.assertIn("Nine", str(choice))
        self.assertIn("✓", str(choice))  # Correct answer marker

    def test_get_text_specific_language(self):
        """Test retrieving choice text in specific language."""
        choice = Choice.objects.create(
            template=self.template, text={"en": "Nine", "pt": "Nove"}, order=0
        )
        self.assertEqual(choice.get_text("en"), "Nine")
        self.assertEqual(choice.get_text("pt"), "Nove")

    def test_get_text_fallback(self):
        """Test choice text fallback logic."""
        choice = Choice.objects.create(
            template=self.template, text={"none": "9", "en": "Nine"}, order=0
        )
        # Request non-existent language, should fallback to "none"
        self.assertEqual(choice.get_text("fr"), "9")

    def test_is_correct_property(self):
        """Test is_correct property."""
        correct = Choice.objects.create(template=self.template, text={"none": "9"}, order=0)
        wrong = Choice.objects.create(template=self.template, text={"none": "10"}, order=1)

        self.assertTrue(correct.is_correct)
        self.assertFalse(wrong.is_correct)

    def test_choice_ordering(self):
        """Test that choices are ordered by order field."""
        choice3 = Choice.objects.create(template=self.template, text={"none": "C"}, order=2)
        choice1 = Choice.objects.create(template=self.template, text={"none": "A"}, order=0)
        choice2 = Choice.objects.create(template=self.template, text={"none": "B"}, order=1)

        choices = list(self.template.choices.all())
        self.assertEqual(choices, [choice1, choice2, choice3])

    def test_choice_cascade_delete(self):
        """Test that deleting question cascades to choices."""
        choice = Choice.objects.create(template=self.template, text={"none": "9"}, order=0)
        question_id = self.template.id
        choice_id = choice.id

        self.template.delete()

        # Question and choice should both be deleted
        self.assertFalse(QuestionTemplate.objects.filter(id=question_id).exists())
        self.assertFalse(Choice.objects.filter(id=choice_id).exists())


class DollarDelimitedChoiceExpressionTests(TestCase):
    """Test restricted dollar-delimited expression evaluation in choices."""

    def setUp(self):
        """Create a reusable question template."""
        self.subject = Subject.objects.create(name="Mathematics")
        self.template = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "$x + y$ remains literal in question text"},
        )

    def create_choice(self, text: str) -> Choice:
        """Create a choice with language-independent text."""
        return Choice.objects.create(
            template=self.template,
            text={"none": text},
            order=0,
        )

    def test_entire_choice_expression_is_evaluated(self):
        """Test a choice containing only an expression."""
        choice = self.create_choice("$x + y$")

        self.assertEqual(choice.get_text(variables={"x": 5, "y": 3}), "8")

    def test_embedded_and_multiple_expressions_are_evaluated(self):
        """Test expressions embedded in surrounding choice text."""
        choice = self.create_choice("Results: $x * y$ and $x - y$")

        self.assertEqual(
            choice.get_text(variables={"x": 5, "y": 3}),
            "Results: 15 and 2",
        )

    def test_set_item_expression_preserves_punctuation(self):
        """Test indexed set values retain commas."""
        choice = self.create_choice("$items[0]$")

        self.assertEqual(
            choice.get_text(variables={"items": ["Paris, France"]}),
            "Paris, France",
        )

    def test_brace_substitution_runs_before_dollar_evaluation(self):
        """Test normal placeholders are resolved before expression evaluation."""
        choice = self.create_choice('$int("{{x}}") / y$')

        self.assertEqual(choice.get_text(variables={"x": 4, "y": 2}), "2.0")

    def test_constant_expression_uses_empty_variable_context(self):
        """Test constant expressions evaluate during static variant generation."""
        choice = self.create_choice("$2 + 2$")

        self.assertEqual(choice.get_text(variables={}), "4")

    def test_invalid_and_unmatched_expressions_remain_literal(self):
        """Test malformed or incomplete expressions fail softly."""
        invalid = self.create_choice("$missing + 1$")
        unmatched = Choice.objects.create(
            template=self.template,
            text={"none": "Price is $5"},
            order=1,
        )

        self.assertEqual(invalid.get_text(variables={"x": 1}), "$missing + 1$")
        self.assertEqual(unmatched.get_text(variables={"x": 1}), "Price is $5")

    def test_question_text_does_not_evaluate_dollar_expressions(self):
        """Test dollar semantics remain limited to choices."""
        self.assertEqual(
            self.template.get_text(variables={"x": 5, "y": 3}),
            "$x + y$ remains literal in question text",
        )


class QuestionChoiceIntegrationTests(TestCase):
    """Integration tests for Question and Choice models."""

    def test_complete_question_workflow(self):
        """Test creating a complete question with choices."""
        subject = Subject.objects.create(name="Mathematics")
        question = QuestionTemplate.objects.create(
            subject=subject,
            text={
                "none": "4 + 5 = ?",
                "en": "What is 4 + 5?",
                "pt": "Quanto é 4 + 5?",
            },
        )

        # Add choices
        correct = Choice.objects.create(template=question, text={"en": "9", "pt": "9"}, order=0)
        wrong1 = Choice.objects.create(template=question, text={"en": "8", "pt": "8"}, order=1)
        wrong2 = Choice.objects.create(template=question, text={"en": "10", "pt": "10"}, order=2)

        # Verify question
        self.assertEqual(question.choice_count, 3)
        self.assertEqual(question.correct_choice, correct)
        self.assertEqual(question.available_languages(), {"none", "en", "pt"})

        # Verify choices
        choices = list(question.choices.all())
        self.assertEqual(len(choices), 3)
        self.assertTrue(choices[0].is_correct)
        self.assertFalse(choices[1].is_correct)
        self.assertFalse(choices[2].is_correct)

    def test_multilingual_fallback_consistency(self):
        """Test that fallback logic is consistent across question and choices."""
        subject = Subject.objects.create(name="Science")
        question = QuestionTemplate.objects.create(
            subject=subject,
            text={"none": "H2O = ?", "en": "What is H2O?"},
        )

        choice = Choice.objects.create(
            template=question, text={"none": "Water", "en": "Water"}, order=0
        )

        # Both should fallback to "none" for unsupported language
        self.assertEqual(question.get_text("fr"), "H2O = ?")
        self.assertEqual(choice.get_text("fr"), "Water")


class VariableGenerationTests(TestCase):
    """Test cases for variable generation (Phase 7, T7.1)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_generate_num_variable_within_bounds(self):
        """Test numeric variable generation stays within min/max bounds."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "What is {{x}}?"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
        )

        # Generate multiple times with different seeds
        for seed in range(20):
            variables = question.generate_variables(seed=seed)
            self.assertIn("x", variables)
            self.assertGreaterEqual(variables["x"], 1)
            self.assertLessEqual(variables["x"], 10)

    def test_generate_num_variable_respects_precision(self):
        """Test numeric variable respects precision parameter."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Value: {{x}}"},
            variables={"x": {"type": "num", "min": 0, "max": 10, "precision": 0.5}},
        )

        variables = question.generate_variables(seed=42)
        x_value = variables["x"]

        # Value should be a multiple of precision (0.5)
        # Check by multiplying by 2 (inverse of 0.5) and verifying it's an integer
        self.assertEqual((x_value * 2) % 1, 0)

    def test_generate_string_variable_length_constraints(self):
        """Test string variable respects min/max length constraints."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Name: {{name}}"},
            variables={"name": {"type": "string", "min_length": 5, "max_length": 10}},
        )

        for seed in range(10):
            variables = question.generate_variables(seed=seed)
            self.assertIn("name", variables)
            name_length = len(variables["name"])
            self.assertGreaterEqual(name_length, 5)
            self.assertLessEqual(name_length, 10)

    def test_generate_set_variable_correct_size(self):
        """Test set variable returns correct number of items."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Items: {{items}}"},
            variables={
                "items": {
                    "type": "set",
                    "items": ["apple", "banana", "cherry", "date", "elderberry"],
                    "size": 3,
                }
            },
        )

        variables = question.generate_variables(seed=42)
        self.assertIn("items", variables)
        self.assertEqual(len(variables["items"]), 3)

        # All items should be from the original set
        for item in variables["items"]:
            self.assertIn(item, ["apple", "banana", "cherry", "date", "elderberry"])

    def test_expression_variable_evaluation(self):
        """Test expression variables evaluate correctly."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "{{a}} + {{b}} = {{sum}}"},
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "sum": {"type": "expression", "formula": "a + b"},
            },
        )

        variables = question.generate_variables(seed=42)
        self.assertIn("sum", variables)
        self.assertEqual(variables["sum"], variables["a"] + variables["b"])

    def test_variables_evaluated_in_order(self):
        """Test that variables are evaluated in definition order."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Result: {{result}}"},
            variables={
                "x": {"type": "num", "min": 1, "max": 5, "precision": 1},
                "y": {"type": "expression", "formula": "x * 2"},
                "result": {"type": "expression", "formula": "y + 10"},
            },
        )

        variables = question.generate_variables(seed=42)
        expected_y = variables["x"] * 2
        expected_result = expected_y + 10

        self.assertEqual(variables["y"], expected_y)
        self.assertEqual(variables["result"], expected_result)


class VariableSubstitutionTests(TestCase):
    """Test cases for variable substitution (Phase 7, T7.2)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_simple_variable_substitution(self):
        """Test simple variable substitution in text."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "What is {{x}}?"},
            variables={"x": {"type": "num", "min": 5, "max": 5, "precision": 1}},
        )

        variables = {"x": 5}
        result = question.get_text(language_code="none", variables=variables)
        self.assertEqual(result, "What is 5?")

    def test_expression_evaluation_in_text(self):
        """Test that expressions in {{}} are evaluated."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "The values are {{items[0]}} and {{items[1]}}"},
            variables={"items": {"type": "set", "items": ["A", "B", "C"], "size": 2}},
        )

        variables = {"items": ["X", "Y"]}
        result = question.get_text(language_code="none", variables=variables)
        self.assertEqual(result, "The values are X and Y")

    def test_multiple_variables_in_text(self):
        """Test multiple variables in the same text."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "{{a}} + {{b}} = {{a + b}}"},
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )

        variables = {"a": 3, "b": 7}
        result = question.get_text(language_code="none", variables=variables)
        self.assertEqual(result, "3 + 7 = 10")

    def test_variable_substitution_preserves_markdown(self):
        """Test that markdown syntax is preserved during substitution."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "**Bold {{x}}** and *italic {{y}}*"},
            variables={
                "x": {"type": "string", "min_length": 4, "max_length": 4},
                "y": {"type": "string", "min_length": 4, "max_length": 4},
            },
        )

        variables = {"x": "text", "y": "word"}
        result = question.get_text(language_code="none", variables=variables)
        self.assertEqual(result, "**Bold text** and *italic word*")

    def test_substitution_in_choices(self):
        """Test variable substitution works in choice text."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "What is {{x}} + {{y}}?"},
            variables={
                "x": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "y": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "sum": {"type": "expression", "formula": "x + y"},
            },
        )

        choice = Choice.objects.create(template=question, text={"none": "{{sum}}"}, order=0)

        variables = {"x": 3, "y": 5, "sum": 8}
        result = choice.get_text(language_code="none", variables=variables)
        self.assertEqual(result, "8")


class VariableValidationTests(TestCase):
    """Test cases for variable validation (Phase 7, T7.3)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_circular_dependency_detected(self):
        """Test that circular dependencies are detected."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Test {{x}}"},
            variables={
                "x": {"type": "expression", "formula": "y + 1"},
                "y": {"type": "expression", "formula": "x + 1"},
            },
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        # Should mention the circular dependency or evaluation error
        self.assertIn("not defined", str(cm.exception).lower())

    def test_undefined_variable_reference_error(self):
        """Test that undefined variable references are caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Value is {{undefined_var}}"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        error_message = str(cm.exception).lower()
        self.assertIn("undefined_var", error_message)

    def test_expression_with_undefined_reference(self):
        """Test that expression referencing undefined variable is caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Result: {{result}}"},
            variables={
                "x": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "result": {"type": "expression", "formula": "undefined_var + 1"},
            },
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        # Should mention that undefined_var is not defined
        error_message = str(cm.exception).lower()
        self.assertTrue("not defined" in error_message or "undefined" in error_message)

    def test_invalid_variable_definition_structure(self):
        """Test that invalid variable definition structure is caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Value: {{x}}"},
            variables={"x": {"type": "num"}},  # Missing min/max
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        error_message = str(cm.exception).lower()
        self.assertTrue(
            "min" in error_message or "max" in error_message or "required" in error_message
        )

    def test_set_size_exceeds_items_error(self):
        """Test that requesting more items than available is caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Items: {{items}}"},
            variables={
                "items": {
                    "type": "set",
                    "items": ["A", "B", "C"],
                    "size": 5,  # More than 3 items available
                }
            },
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        error_message = str(cm.exception).lower()
        self.assertTrue(
            "size" in error_message or "items" in error_message or "exceed" in error_message
        )

    def test_min_greater_than_max_error(self):
        """Test that min > max is caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Value: {{x}}"},
            variables={"x": {"type": "num", "min": 10, "max": 5, "precision": 1}},
        )

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        error_message = str(cm.exception).lower()
        self.assertTrue(
            "min" in error_message or "max" in error_message or "greater" in error_message
        )

    def test_undefined_variable_in_choice_text(self):
        """Test that undefined variables in choice text are caught."""
        question = QuestionTemplate(
            subject=self.subject,
            text={"none": "Question with {{x}}"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
        )
        question.save()

        # Add choice with undefined variable
        Choice.objects.create(template=question, text={"none": "Answer: {{undefined}}"}, order=0)

        with self.assertRaises(ValidationError) as cm:
            question.full_clean()

        error_message = str(cm.exception).lower()
        self.assertIn("undefined", error_message)


class ValidationRulesTests(TestCase):
    """Test cases for validation rules functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.subject = Subject.objects.create(name="Math")

    def test_validate_rules_all_pass(self):
        """Test that validation passes when all rules return True."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 5, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 4, "precision": 1},
            },
            validation_rules=["a > b", "a + b > 0"],
        )

        variables = question.generate_variables(seed=42)
        self.assertIn("a", variables)
        self.assertIn("b", variables)
        self.assertGreater(variables["a"], variables["b"])

    def test_validate_rules_one_fails(self):
        """Test that validation fails when one rule returns False."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )

        variables = {"a": 5}

        # Rule that should pass
        question.validation_rules = ["a > 0"]
        self.assertTrue(question._validate_rules(variables))

        # Rule that should fail
        question.validation_rules = ["a > 10"]
        self.assertFalse(question._validate_rules(variables))

    def test_validate_rules_empty(self):
        """Test that validation passes when no rules are defined."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={"a": {"type": "num", "min": 1, "max": 10, "precision": 1}},
            validation_rules=[],
        )

        variables = {"a": 5}
        self.assertTrue(question._validate_rules(variables))

    def test_validate_rules_syntax_error(self):
        """Test that invalid rule syntax is treated as validation failure."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={"a": {"type": "num", "min": 1, "max": 10, "precision": 1}},
        )

        variables = {"a": 5}

        # Invalid syntax should return False (not raise exception)
        question.validation_rules = ["a >>>> b"]
        self.assertFalse(question._validate_rules(variables))

    def test_generate_variables_with_validation(self):
        """Test successful variable generation with validation rules."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 5, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 4, "precision": 1},
            },
            validation_rules=["a > b"],
        )

        # Should generate valid variables
        variables = question.generate_variables(seed=42)
        self.assertGreater(variables["a"], variables["b"])

    def test_generate_variables_max_retries(self):
        """Test that ValidationError is raised after max attempts."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 1, "max": 5, "precision": 1},
            },
            validation_rules=["a > 10"],  # Impossible rule
        )

        with self.assertRaises(ValidationError) as cm:
            question.generate_variables(seed=42, max_validation_attempts=10)

        error_message = str(cm.exception)
        self.assertIn("10 attempts", error_message)
        self.assertIn("too restrictive", error_message)

    def test_validation_rule_undefined_variable(self):
        """Test that rule referencing undefined variable fails validation."""
        question = QuestionTemplate.objects.create(
            title="Test",
            text={"none": "Test"},
            subject=self.subject,
            variables={"a": {"type": "num", "min": 1, "max": 10, "precision": 1}},
            validation_rules=["b > 0"],  # 'b' is not defined
        )

        variables = {"a": 5}
        self.assertFalse(question._validate_rules(variables))

    def test_complex_validation_rules(self):
        """Test complex validation rules like triangle inequality and integer results."""
        # Triangle inequality
        question = QuestionTemplate.objects.create(
            title="Triangle",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "c": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
            validation_rules=[
                "a + b > c",
                "b + c > a",
                "c + a > b",
            ],
        )

        variables = question.generate_variables(seed=42)
        # Verify triangle inequality
        self.assertGreater(variables["a"] + variables["b"], variables["c"])
        self.assertGreater(variables["b"] + variables["c"], variables["a"])
        self.assertGreater(variables["c"] + variables["a"], variables["b"])

        # Integer result validation
        question2 = QuestionTemplate.objects.create(
            title="Integer Result",
            text={"none": "Test"},
            subject=self.subject,
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "result": {"type": "expression", "formula": "a / b"},
            },
            validation_rules=["result % 1 == 0"],  # Ensure integer result
        )

        variables2 = question2.generate_variables(seed=43)
        self.assertEqual(variables2["result"] % 1, 0)


class VariableIntegrationTests(TestCase):
    """Integration tests for variables (Phase 7, T7.4)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")

    def test_create_question_with_variables(self):
        """Test creating a question with variables."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Variable Question",
            text={"none": "What is {{x}} + {{y}}?"},
            variables={
                "x": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "y": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )

        question.full_clean()  # Should not raise

        # Generate variables and verify substitution works
        variables = question.generate_variables(seed=42)
        rendered_text = question.get_text(language_code="none", variables=variables)

        self.assertNotIn("{{", rendered_text)  # No variable markers left
        self.assertIn(str(int(variables["x"])), rendered_text)

    def test_edit_question_add_variables(self):
        """Test adding variables to existing question."""
        # Create question without variables
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Simple Question", text={"none": "What is 2 + 2?"}
        )

        # Update to add variables
        question.text = {"none": "What is {{a}} + {{b}}?"}
        question.variables = {
            "a": {"type": "num", "min": 1, "max": 5, "precision": 1},
            "b": {"type": "num", "min": 1, "max": 5, "precision": 1},
        }
        question.save()
        question.full_clean()  # Should not raise

        # Verify variables work
        variables = question.generate_variables(seed=0)
        self.assertIn("a", variables)
        self.assertIn("b", variables)

    def test_question_without_variables_still_works(self):
        """Test backward compatibility - questions without variables."""
        question = QuestionTemplate.objects.create(
            subject=self.subject, title="Static Question", text={"none": "What is 2 + 2?"}
        )

        # Should work without variables
        question.full_clean()
        text = question.get_text(language_code="none")
        self.assertEqual(text, "What is 2 + 2?")

        # generate_variables should return empty dict
        variables = question.generate_variables()
        self.assertEqual(variables, {})

    def test_preview_generates_different_instances(self):
        """Test that different seeds generate different variable values."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"none": "Value: {{x}}"},
            variables={"x": {"type": "num", "min": 1, "max": 100, "precision": 1}},
        )

        # Generate with different seeds
        vars1 = question.generate_variables(seed=0)
        vars2 = question.generate_variables(seed=1)
        vars3 = question.generate_variables(seed=100)

        # At least some should be different (with 100 options, very unlikely all same)
        values = [vars1["x"], vars2["x"], vars3["x"]]
        self.assertGreater(len(set(values)), 1, "Different seeds should produce different values")

    def test_multilingual_with_variables(self):
        """Test that variables work with multilingual text."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            text={"en": "What is {{x}} + {{y}}?", "pt": "Quanto é {{x}} + {{y}}?"},
            variables={
                "x": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "y": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )

        variables = question.generate_variables(seed=42)

        # Both languages should have variables substituted
        en_text = question.get_text(language_code="en", variables=variables)
        pt_text = question.get_text(language_code="pt", variables=variables)

        self.assertNotIn("{{", en_text)
        self.assertNotIn("{{", pt_text)
        self.assertIn(str(int(variables["x"])), en_text)
        self.assertIn(str(int(variables["x"])), pt_text)


class VariableFormTests(TestCase):
    """Form tests for variables (Phase 7, T7.5)."""

    def setUp(self):
        """Set up test data."""
        from apps.questions.forms import QuestionForm

        self.form_class = QuestionForm
        self.subject = Subject.objects.create(name="Mathematics")

    def test_question_form_accepts_variables_json(self):
        """Test that QuestionForm accepts and processes variables_json."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "What is {{x}}?"}',
            "variables_json": '{"x": {"type": "num", "min": 1, "max": 10, "precision": 1}}',
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_question_form_validates_variables(self):
        """Test that QuestionForm validates variable definitions during save."""
        # Invalid: missing required fields
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "What is {{x}}?"}',
            "variables_json": '{"x": {"type": "num"}}',  # Missing min/max
        }

        form = self.form_class(data=form_data)
        # Form may be valid initially, but save should trigger model validation
        if form.is_valid():
            with self.assertRaises(ValidationError):
                question = form.save(commit=False)
                question.full_clean()  # This triggers validation

    def test_question_form_saves_variables_to_model(self):
        """Test that QuestionForm saves variables to model."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "What is {{x}}?"}',
            "variables_json": '{"x": {"type": "num", "min": 1, "max": 10, "precision": 1}}',
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        question = form.save()
        self.assertIsNotNone(question.variables)
        self.assertIn("x", question.variables)
        self.assertEqual(question.variables["x"]["type"], "num")

    def test_question_form_empty_variables_json(self):
        """Test that form handles empty/missing variables_json."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "Simple question"}',
            "variables_json": "",
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        question = form.save()
        # Empty variables_json should result in empty dict or None
        self.assertIn(question.variables, [None, {}, "{}"])

    def test_question_form_edit_mode_loads_variables(self):
        """Test that form loads existing variables in edit mode."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Existing Question",
            text={"none": "What is {{x}}?"},
            variables={"x": {"type": "num", "min": 1, "max": 10, "precision": 1}},
        )

        form = self.form_class(instance=question)

        # Form should have initial data for variables_json
        initial_variables = form.initial.get("variables_json")
        self.assertIsNotNone(initial_variables)

        # Convert to dict if it's a string
        if isinstance(initial_variables, str):
            import json

            initial_variables = json.loads(initial_variables)

        self.assertIn("x", initial_variables)


class SetVariableFormTests(TestCase):
    """Regression tests for one-item-per-line set variable input."""

    def setUp(self):
        """Create a subject and a set variable with comma-containing items."""
        self.subject = Subject.objects.create(name="Geography")
        self.question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Cities",
            text={"none": "Choose {{cities[0]}}"},
            variables={
                "cities": {
                    "type": "set",
                    "items": ["Paris, France", "Porto, Portugal", "London"],
                    "size": 1,
                }
            },
        )

    def test_set_variable_uses_one_item_per_line_textarea(self):
        """Test the set editor communicates newline-separated input."""
        response = self.client.get(reverse("questions:edit", args=[self.question.pk]))

        self.assertContains(response, 'class="form-control form-control-sm var-items"')
        self.assertContains(response, 'placeholder="One item per line"')
        self.assertContains(response, "Commas inside a line are preserved")

    def test_set_variable_script_preserves_commas_inside_lines(self):
        """Test JavaScript uses newline boundaries for loading and saving."""
        script_path = (
            Path(__file__).parent
            / "static"
            / "questions"
            / "js"
            / "question_form.js"
        )
        script = script_path.read_text()

        self.assertIn("config.items.join('\\n')", script)
        self.assertIn("itemsText.split(/\\r?\\n/)", script)
        self.assertNotIn("itemsText.split(',')", script)

    def test_form_preserves_comma_containing_set_items(self):
        """Test the backend stores complete comma-containing array items."""
        from apps.questions.forms import QuestionForm

        form = QuestionForm(
            data={
                "subject": self.subject.id,
                "title": "Cities",
                "text": '{"none": "Choose {{cities[0]}}"}',
                "variables_json": json.dumps(self.question.variables),
                "state": "draft",
            },
            instance=self.question,
        )

        self.assertTrue(form.is_valid(), form.errors)
        question = form.save()
        self.assertEqual(
            question.variables["cities"]["items"],
            ["Paris, France", "Porto, Portugal", "London"],
        )

    def test_set_generator_preserves_item_punctuation(self):
        """Test generation returns comma-containing items unchanged."""
        self.question.variables["cities"]["items"] = ["Paris, France"]
        self.question.save()

        generated = self.question.generate_variables(seed=1)

        self.assertEqual(generated["cities"], ["Paris, France"])


class ValidationRulesFormTests(TestCase):
    """Form tests for validation rules."""

    def setUp(self):
        """Set up test data."""
        from apps.questions.forms import QuestionForm

        self.form_class = QuestionForm
        self.subject = Subject.objects.create(name="Mathematics")

    def test_validation_rules_field_valid_input(self):
        """Test that form accepts valid validation rules."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "What is {{a}} + {{b}}?"}',
            "variables_json": '{"a": {"type": "num", "min": 1, "max": 10, "precision": 1}, "b": {"type": "num", "min": 1, "max": 10, "precision": 1}}',
            "validation_rules_json": '["a > b", "a + b > 0"]',
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        question = form.save()
        self.assertEqual(len(question.validation_rules), 2)
        self.assertIn("a > b", question.validation_rules)

    def test_validation_rules_field_invalid_syntax(self):
        """Test that form rejects invalid syntax in rules."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "Test"}',
            "variables_json": "{}",
            "validation_rules_json": '["a >>>> b"]',  # Invalid syntax
        }

        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("validation_rules_json", form.errors)

    def test_validation_rules_serialization(self):
        """Test that validation rules JSON encoding/decoding works."""
        # Test with list input
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "Test"}',
            "variables_json": "{}",
            "validation_rules_json": ["a > 0", "b < 100"],  # List directly
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        question = form.save()
        self.assertEqual(question.validation_rules, ["a > 0", "b < 100"])

    def test_validation_rules_empty(self):
        """Test that empty validation rules list is handled correctly."""
        form_data = {
            "subject": self.subject.id,
            "title": "Test Question",
            "text": '{"none": "Test"}',
            "variables_json": "{}",
            "validation_rules_json": "",  # Empty
            "state": "draft",
        }

        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        question = form.save()
        self.assertEqual(question.validation_rules, [])

    def test_validation_rules_edit_mode_loads(self):
        """Test that form loads existing validation rules in edit mode."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Existing Question",
            text={"none": "Test"},
            variables={"a": {"type": "num", "min": 1, "max": 10, "precision": 1}},
            validation_rules=["a > 0", "a < 100"],
        )

        form = self.form_class(instance=question)

        # Form should have initial data for validation_rules_json
        initial_rules = form.initial.get("validation_rules_json")
        self.assertIsNotNone(initial_rules)
        self.assertEqual(initial_rules, ["a > 0", "a < 100"])


class ValidationRulesPreviewTests(TestCase):
    """Tests for validation rules in preview view (Phase 4)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Math")

    def test_preview_with_valid_rules(self):
        """Test that preview works when validation rules can be satisfied."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Valid Rules Question",
            text={"none": "What is {{a}} + {{b}}?"},
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
            validation_rules=["a > b"],  # Should succeed eventually
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("preview_instance", response.context)

        # Should have successfully generated variables
        preview = response.context["preview_instance"]
        self.assertNotIn("error", preview)
        self.assertIn("variables", preview)
        self.assertIn("a", preview["variables"])
        self.assertIn("b", preview["variables"])
        self.assertGreater(preview["variables"]["a"], preview["variables"]["b"])

    def test_preview_with_impossible_rules(self):
        """Test that preview shows helpful error when rules can't be satisfied."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Impossible Rules Question",
            text={"none": "Test"},
            variables={
                "x": {"type": "num", "min": 1, "max": 5, "precision": 1},
            },
            validation_rules=["x > 10", "x < 3"],  # Impossible with range 1-5
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("preview_instance", response.context)

        # Should have error information
        preview = response.context["preview_instance"]
        self.assertIn("error", preview)
        self.assertTrue(preview.get("validation_error", False))
        self.assertEqual(preview.get("error_type"), "validation_rules")

    def test_preview_without_validation_rules(self):
        """Test that preview works normally when no validation rules are set."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="No Rules Question",
            text={"none": "What is {{a}}?"},
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
            validation_rules=[],  # No rules
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("preview_instance", response.context)

        # Should work without errors
        preview = response.context["preview_instance"]
        self.assertNotIn("error", preview)
        self.assertIn("variables", preview)

    def test_preview_with_conflicting_rules(self):
        """Test preview with rules that conflict with variable ranges."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Conflicting Rules",
            text={"none": "{{a}}, {{b}}, {{c}}"},
            variables={
                "a": {"type": "num", "min": 1, "max": 100, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 100, "precision": 1},
                "c": {"type": "num", "min": 1, "max": 100, "precision": 1},
            },
            validation_rules=[
                "a > b",
                "b > c",
                "c > a",  # Creates circular dependency: a > b > c > a (impossible)
            ],
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Should show validation error
        preview = response.context["preview_instance"]
        self.assertIn("error", preview)
        self.assertTrue(preview.get("validation_error"))


class ValidationRulesIntegrationTests(TestCase):
    """Integration tests for validation rules through views (Phase 5)."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Math")

    def test_question_create_with_validation_rules(self):
        """Test creating a question with validation rules via form."""
        url = reverse("questions:create")
        form_data = {
            "subject": self.subject.id,
            "title": "Triangle Inequality Question",
            "text": '{"none": "Triangle with sides {{a}}, {{b}}, {{c}}"}',
            "state": "draft",
            "variables_json": json.dumps(
                {
                    "a": {"type": "num", "min": 1, "max": 20, "precision": 1},
                    "b": {"type": "num", "min": 1, "max": 20, "precision": 1},
                    "c": {"type": "num", "min": 1, "max": 20, "precision": 1},
                }
            ),
            "validation_rules_json": json.dumps(
                [
                    "a + b > c",
                    "b + c > a",
                    "a + c > b",
                ]
            ),
            # Add required choices
            "choices-0-text": '{"none": "Valid triangle"}',
            "choices-0-is_correct": "on",
            "choices-1-text": '{"none": "Invalid triangle"}',
        }

        response = self.client.post(url, form_data)

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify question created with validation rules
        question = QuestionTemplate.objects.get(title="Triangle Inequality Question")
        self.assertEqual(len(question.validation_rules), 3)
        self.assertIn("a + b > c", question.validation_rules)

        # Verify variables can be generated with rules
        variables = question.generate_variables()
        self.assertIn("a", variables)
        self.assertIn("b", variables)
        self.assertIn("c", variables)

        # Verify triangle inequality holds
        a, b, c = variables["a"], variables["b"], variables["c"]
        self.assertGreater(a + b, c)
        self.assertGreater(b + c, a)
        self.assertGreater(a + c, b)

    def test_question_update_with_validation_rules(self):
        """Test updating an existing question to add validation rules."""
        # Create question without validation rules
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Simple Question",
            text={"none": "What is {{a}} + {{b}}?"},
            variables={
                "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
        )

        # Add choices to the question
        Choice.objects.create(template=question, text={"none": "Correct"}, order=0)
        Choice.objects.create(template=question, text={"none": "Incorrect"}, order=1)

        url = reverse("questions:edit", args=[question.pk])
        form_data = {
            "subject": self.subject.id,
            "title": "Updated Question",
            "text": '{"none": "What is {{a}} + {{b}}?"}',
            "state": "draft",
            "variables_json": json.dumps(
                {
                    "a": {"type": "num", "min": 1, "max": 10, "precision": 1},
                    "b": {"type": "num", "min": 1, "max": 10, "precision": 1},
                }
            ),
            "validation_rules_json": json.dumps(["a > b"]),  # Add validation rule
            # Include existing choices
            "choices-0-text": '{"none": "Correct"}',
            "choices-0-is_correct": "on",
            "choices-1-text": '{"none": "Incorrect"}',
        }

        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 302)

        # Verify validation rule was added
        question.refresh_from_db()
        self.assertEqual(question.validation_rules, ["a > b"])

        # Verify rule is enforced
        variables = question.generate_variables()
        self.assertGreater(variables["a"], variables["b"])

    def test_question_preview_with_validation_rules(self):
        """Test that preview respects validation rules."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Ordered Numbers",
            text={"none": "Numbers: {{x}}, {{y}}, {{z}}"},
            variables={
                "x": {"type": "num", "min": 1, "max": 50, "precision": 1},
                "y": {"type": "num", "min": 1, "max": 50, "precision": 1},
                "z": {"type": "num", "min": 1, "max": 50, "precision": 1},
            },
            validation_rules=["x < y", "y < z"],  # Enforce ordering
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Should have successfully generated variables
        preview = response.context["preview_instance"]
        self.assertNotIn("error", preview)
        self.assertIn("variables", preview)

        # Verify ordering is maintained
        x = preview["variables"]["x"]
        y = preview["variables"]["y"]
        z = preview["variables"]["z"]
        self.assertLess(x, y)
        self.assertLess(y, z)

    def test_question_preview_validation_error(self):
        """Test that preview shows error when validation rules fail."""
        question = QuestionTemplate.objects.create(
            subject=self.subject,
            title="Impossible Question",
            text={"none": "Value: {{n}}"},
            variables={
                "n": {"type": "num", "min": 1, "max": 10, "precision": 1},
            },
            validation_rules=["n > 20"],  # Impossible with range 1-10
        )

        from django.urls import reverse

        url = reverse("questions:preview", args=[question.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Should show error
        preview = response.context["preview_instance"]
        self.assertIn("error", preview)
        self.assertTrue(preview.get("validation_error"))
        self.assertEqual(preview.get("error_type"), "validation_rules")
