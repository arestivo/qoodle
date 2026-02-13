"""App configuration for the data app."""

from django.apps import AppConfig


class DataConfig(AppConfig):
    """Configuration for the data management app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.data"
    verbose_name = "Data Management"
