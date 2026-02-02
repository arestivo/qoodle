"""Subject app configuration."""

from django.apps import AppConfig


class SubjectsConfig(AppConfig):
    """Configuration for the subjects app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.subjects"
    verbose_name = "Subjects"
