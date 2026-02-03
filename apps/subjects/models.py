"""Models for the subjects app."""

from django.db import models
from django.urls import reverse

from apps.common.models import UUIDModel


class Subject(UUIDModel):
    """
    Hierarchical subject model for organizing quiz questions.

    Subjects can have a parent subject, creating a tree structure
    for organizing questions by topic and sub-topic.
    """

    name = models.CharField(
        max_length=200,
        help_text="Name of the subject or topic",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent subject (leave empty for root-level subjects)",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the subject",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_subject_name_per_parent",
            )
        ]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self) -> str:
        """Return string representation of the subject."""
        return self.name

    def get_absolute_url(self) -> str:
        """Return the URL for this subject."""
        return reverse("subjects:detail", kwargs={"pk": self.pk})

    def get_children(self):
        """Return immediate child subjects."""
        return self.children.all()

    def get_question_count(self) -> int:
        """Return count of questions directly assigned to this subject."""
        return self.questions.count()

    def get_ancestors(self):
        """
        Return all parent subjects up to the root.

        Returns a list ordered from root to immediate parent.
        """
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """
        Return all child subjects recursively.

        Returns a flat list of all descendants at any level.
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    @property
    def depth(self) -> int:
        """Return the depth level of this subject in the tree."""
        return len(self.get_ancestors())

    @property
    def is_root(self) -> bool:
        """Check if this is a root-level subject."""
        return self.parent is None

    def has_children(self) -> bool:
        """Check if this subject has any child subjects."""
        return self.children.exists()

    def get_full_path(self, separator: str = " > ") -> str:
        """
        Return the full path from root to this subject.

        Args:
            separator: String to use between subject names (default: " > ")

        Returns:
            Full path string like "Math > Algebra > Equations"
        """
        ancestors = self.get_ancestors()
        path_parts = [ancestor.name for ancestor in ancestors] + [self.name]
        return separator.join(path_parts)
