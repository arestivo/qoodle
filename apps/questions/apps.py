"""Questions app configuration."""

from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    """Configuration for the questions app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.questions"
    verbose_name = "Questions"
