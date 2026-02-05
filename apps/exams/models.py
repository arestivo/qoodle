"""Models for exam management.

This module defines the core models for creating and managing exams:
- Exam: The top-level container for an exam
- QuestionPool: An ordered pool of questions within an exam
- QuestionPoolTemplate: Links question templates to pools with version counts
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import UUIDModel


class Exam(UUIDModel):
    """An exam composed of ordered question pools."""

    GRADING_MODE_CHOICES = [
        ("single", "Single Choice"),
        ("multi", "Multiple Choice"),
    ]

    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    grading_mode = models.CharField(max_length=10, choices=GRADING_MODE_CHOICES, default="single", help_text=("Single Choice: Student can only choose one correct answer. Multiple Choice: Student can choose multiple correct answers."))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self) -> str:
        return self.title

    def get_grading_mode_display_verbose(self) -> str:
        """Get detailed grading mode description."""
        if self.grading_mode == "single":
            return "Single Choice"
        return "Multiple Choice"


class QuestionPool(UUIDModel):
    """Ordered slot in an exam containing alternative question templates."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="pools")
    order = models.PositiveIntegerField()
    default_grade = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1.0"), validators=[MinValueValidator(Decimal("0.1"))], help_text="Point value for questions in this pool (default: 1.0)")
    question_templates = models.ManyToManyField(
        "questions.QuestionTemplate",
        through="QuestionPoolTemplate",
        related_name="pools",
    )

    class Meta:
        ordering = ["order"]
        unique_together = [("exam", "order")]
        verbose_name = "Question Pool"
        verbose_name_plural = "Question Pools"

    def __str__(self) -> str:
        return f"{self.exam.title} - Pool {self.order}"


class QuestionPoolTemplate(UUIDModel):
    """Through table linking pools to templates with version count."""

    pool = models.ForeignKey(QuestionPool, on_delete=models.CASCADE, related_name="pool_templates")
    template = models.ForeignKey(
        "questions.QuestionTemplate",
        on_delete=models.CASCADE,
        related_name="pool_memberships",
    )
    number_of_versions = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [("pool", "template")]
        verbose_name = "Question Pool Template"
        verbose_name_plural = "Question Pool Templates"

    def __str__(self) -> str:
        return f"{self.pool} - {self.template.title} (x{self.number_of_versions})"
