"""Admin configuration for the subjects app."""

from django.contrib import admin

from apps.subjects.models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for Subject model."""

    list_display = ["name", "parent", "question_count", "created_at"]
    list_filter = ["parent", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = [
        (
            "Subject Information",
            {
                "fields": ["name", "parent", "description"],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("parent")
