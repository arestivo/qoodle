"""Models for exam management.

This module defines the core models for creating and managing exams:
- Exam: The top-level container for an exam
- QuestionPool: An ordered pool of questions within an exam
- QuestionPoolTemplate: Links question templates to pools with version counts
"""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import UUIDModel


class Exam(UUIDModel):
    """An exam composed of ordered question pools."""

    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self) -> str:
        return self.title


class QuestionPool(UUIDModel):
    """Ordered slot in an exam containing alternative question templates."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="pools")
    order = models.PositiveIntegerField()
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
