"""Tests for the questions app."""

import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.questions.models import Choice, Question, validate_multilingual_text
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
        question = Question.objects.create(subject=self.subject, text={"none": "What is 4 + 5?"})
        self.assertIsInstance(question.id, uuid.UUID)
        self.assertEqual(question.subject, self.subject)
        self.assertEqual(question.text, {"none": "What is 4 + 5?"})
        self.assertIsNotNone(question.created_at)

    def test_question_str_representation(self):
        """Test string representation of question."""
        question = Question.objects.create(subject=self.subject, text={"en": "What is the answer?"})
        self.assertIn("What is the answer?", str(question))

    def test_get_text_specific_language(self):
        """Test retrieving text in specific language."""
        question = Question.objects.create(
            subject=self.subject,
            text={"en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"},
        )
        self.assertEqual(question.get_text("en"), "What is 4 + 5?")
        self.assertEqual(question.get_text("pt"), "Quanto é 4 + 5?")

    def test_get_text_fallback_to_none(self):
        """Test fallback to language-independent text."""
        question = Question.objects.create(
            subject=self.subject,
            text={"none": "4 + 5 = ?", "en": "What is 4 + 5?"},
        )
        # Request non-existent language, should fallback to "none"
        self.assertEqual(question.get_text("fr"), "4 + 5 = ?")

    def test_get_text_fallback_to_any_language(self):
        """Test fallback to any available language."""
        question = Question.objects.create(subject=self.subject, text={"pt": "Quanto é 4 + 5?", "es": "¿Cuánto es 4 + 5?"})
        # No "none" key, should fallback to first alphabetically
        result = question.get_text("fr")
        self.assertIn(result, ["Quanto é 4 + 5?", "¿Cuánto es 4 + 5?"])

    def test_get_text_no_language_specified(self):
        """Test getting text with no language specified."""
        question = Question.objects.create(
            subject=self.subject,
            text={"none": "4 + 5 = ?", "en": "What is 4 + 5?"},
        )
        # Should return "none" when no language specified
        self.assertEqual(question.get_text(), "4 + 5 = ?")

    def test_get_text_no_none_key(self):
        """Test getting text with no language specified and no none key."""
        question = Question.objects.create(subject=self.subject, text={"en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"})
        # Should fallback to first alphabetically
        self.assertEqual(question.get_text(), "What is 4 + 5?")

    def test_available_languages(self):
        """Test retrieving available languages."""
        question = Question.objects.create(
            subject=self.subject,
            text={"none": "Text", "en": "English", "pt": "Portuguese"},
        )
        languages = question.available_languages()
        self.assertEqual(languages, {"none", "en", "pt"})

    def test_get_all_texts(self):
        """Test retrieving all text versions."""
        text_dict = {"none": "Text", "en": "English"}
        question = Question.objects.create(subject=self.subject, text=text_dict)
        self.assertEqual(question.get_all_texts(), text_dict)

    def test_choice_count(self):
        """Test choice count property."""
        question = Question.objects.create(subject=self.subject, text={"none": "Question?"})
        self.assertEqual(question.choice_count, 0)

        Choice.objects.create(question=question, text={"none": "Choice 1"}, order=0)
        Choice.objects.create(question=question, text={"none": "Choice 2"}, order=1)
        self.assertEqual(question.choice_count, 2)

    def test_correct_choice_property(self):
        """Test correct_choice property returns first choice."""
        question = Question.objects.create(subject=self.subject, text={"none": "Question?"})
        correct = Choice.objects.create(question=question, text={"none": "Correct"}, order=0)
        Choice.objects.create(question=question, text={"none": "Wrong"}, order=1)

        self.assertEqual(question.correct_choice, correct)

    def test_question_subject_protect(self):
        """Test that deleting subject is protected if it has questions."""
        question = Question.objects.create(subject=self.subject, text={"none": "Question?"})
        # Attempting to delete subject should raise ProtectedError
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.subject.delete()


class ChoiceModelTests(TestCase):
    """Test cases for the Choice model."""

    def setUp(self):
        """Set up test data."""
        self.subject = Subject.objects.create(name="Mathematics")
        self.question = Question.objects.create(subject=self.subject, text={"none": "What is 4 + 5?"})

    def test_choice_creation(self):
        """Test creating a basic choice."""
        choice = Choice.objects.create(question=self.question, text={"none": "9"}, order=0)
        self.assertIsInstance(choice.id, uuid.UUID)
        self.assertEqual(choice.question, self.question)
        self.assertEqual(choice.text, {"none": "9"})
        self.assertEqual(choice.order, 0)

    def test_choice_str_representation(self):
        """Test string representation of choice."""
        choice = Choice.objects.create(question=self.question, text={"en": "Nine"}, order=0)
        self.assertIn("Nine", str(choice))
        self.assertIn("✓", str(choice))  # Correct answer marker

    def test_get_text_specific_language(self):
        """Test retrieving choice text in specific language."""
        choice = Choice.objects.create(question=self.question, text={"en": "Nine", "pt": "Nove"}, order=0)
        self.assertEqual(choice.get_text("en"), "Nine")
        self.assertEqual(choice.get_text("pt"), "Nove")

    def test_get_text_fallback(self):
        """Test choice text fallback logic."""
        choice = Choice.objects.create(question=self.question, text={"none": "9", "en": "Nine"}, order=0)
        # Request non-existent language, should fallback to "none"
        self.assertEqual(choice.get_text("fr"), "9")

    def test_is_correct_property(self):
        """Test is_correct property."""
        correct = Choice.objects.create(question=self.question, text={"none": "9"}, order=0)
        wrong = Choice.objects.create(question=self.question, text={"none": "10"}, order=1)

        self.assertTrue(correct.is_correct)
        self.assertFalse(wrong.is_correct)

    def test_choice_ordering(self):
        """Test that choices are ordered by order field."""
        choice3 = Choice.objects.create(question=self.question, text={"none": "C"}, order=2)
        choice1 = Choice.objects.create(question=self.question, text={"none": "A"}, order=0)
        choice2 = Choice.objects.create(question=self.question, text={"none": "B"}, order=1)

        choices = list(self.question.choices.all())
        self.assertEqual(choices, [choice1, choice2, choice3])

    def test_choice_cascade_delete(self):
        """Test that deleting question cascades to choices."""
        choice = Choice.objects.create(question=self.question, text={"none": "9"}, order=0)
        question_id = self.question.id
        choice_id = choice.id

        self.question.delete()

        # Question and choice should both be deleted
        self.assertFalse(Question.objects.filter(id=question_id).exists())
        self.assertFalse(Choice.objects.filter(id=choice_id).exists())


class QuestionChoiceIntegrationTests(TestCase):
    """Integration tests for Question and Choice models."""

    def test_complete_question_workflow(self):
        """Test creating a complete question with choices."""
        subject = Subject.objects.create(name="Mathematics")
        question = Question.objects.create(
            subject=subject,
            text={
                "none": "4 + 5 = ?",
                "en": "What is 4 + 5?",
                "pt": "Quanto é 4 + 5?",
            },
        )

        # Add choices
        correct = Choice.objects.create(question=question, text={"en": "9", "pt": "9"}, order=0)
        wrong1 = Choice.objects.create(question=question, text={"en": "8", "pt": "8"}, order=1)
        wrong2 = Choice.objects.create(question=question, text={"en": "10", "pt": "10"}, order=2)

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
        question = Question.objects.create(
            subject=subject,
            text={"none": "H2O = ?", "en": "What is H2O?"},
        )

        choice = Choice.objects.create(question=question, text={"none": "Water", "en": "Water"}, order=0)

        # Both should fallback to "none" for unsupported language
        self.assertEqual(question.get_text("fr"), "H2O = ?")
        self.assertEqual(choice.get_text("fr"), "Water")
