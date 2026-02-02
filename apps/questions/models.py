"""Models for the questions app."""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.common.models import UUIDModel
from apps.subjects.models import Subject


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


class Question(UUIDModel):
    """
    Quiz question with multilingual support.

    Questions belong to a subject and contain text that can be provided
    in multiple languages. The first choice (order=0) is always the correct answer.
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="questions",
        help_text="Subject this question belongs to",
    )
    title = models.CharField(
        max_length=200,
        default="no title",
        help_text="Short title to identify this question",
    )
    text = models.JSONField(
        help_text="Question text in multiple languages (JSON)",
        validators=[validate_multilingual_text],
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        indexes = [
            models.Index(fields=["subject", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the question."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the URL for this question."""
        return reverse("questions:preview", kwargs={"pk": self.pk})

    def get_text(self, language_code: str = None) -> str:
        """
        Get text for specific language with fallback.

        Fallback order:
        1. Requested language (if specified and exists)
        2. Language-independent version ("none" key)
        3. First available language (alphabetically)

        Args:
            language_code: Optional language code to retrieve

        Returns:
            Question text in requested or fallback language

        Raises:
            ValueError: If no text available in any language
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

    def available_languages(self) -> set[str]:
        """Return set of all language codes used in this question."""
        return set(self.text.keys()) if self.text else set()

    def get_all_texts(self) -> dict[str, str]:
        """Return dict of all language versions."""
        return dict(self.text) if self.text else {}

    @property
    def choice_count(self) -> int:
        """Return the number of choices for this question."""
        return self.choices.count()

    @property
    def correct_choice(self):
        """Return the correct choice (first choice with order=0)."""
        return self.choices.filter(order=0).first()


class Choice(UUIDModel):
    """
    Multiple choice option with multilingual support.

    Important: The first choice (order=0) is always the correct answer.
    When displaying questions to students, choices should be randomized.
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        help_text="Question this choice belongs to",
    )
    text = models.JSONField(
        help_text="Choice text in multiple languages (JSON)",
        validators=[validate_multilingual_text],
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of choice (0 = correct answer)",
    )

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    def __str__(self) -> str:
        """Return string representation of the choice."""
        try:
            text = self.get_text()[:50]
            return f"{text} {'✓' if self.is_correct else ''}"
        except (ValueError, KeyError):
            return f"Choice {self.id}"

    def get_text(self, language_code: str = None) -> str:
        """
        Get text for specific language with fallback.

        Fallback order:
        1. Requested language (if specified and exists)
        2. Language-independent version ("none" key)
        3. First available language (alphabetically)

        Args:
            language_code: Optional language code to retrieve

        Returns:
            Choice text in requested or fallback language

        Raises:
            ValueError: If no text available in any language
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

    @property
    def is_correct(self) -> bool:
        """Return True if this is the correct answer (order=0)."""
        return self.order == 0
