"""Common models for the Qoodle application."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamp fields.

    All models in the system should extend this base class to ensure
    consistent UUID usage and automatic timestamp tracking.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this object",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this object was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this object was last updated",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
