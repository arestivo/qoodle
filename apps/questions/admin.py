"""Admin configuration for the questions app."""

from django.contrib import admin

from apps.questions.models import Choice, QuestionTemplate


class ChoiceInline(admin.TabularInline):
    """Inline admin for choices."""

    model = Choice
    extra = 0
    fields = ["text", "order"]


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    """Admin interface for QuestionTemplate model."""

    list_display = ["title", "subject", "choice_count", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["title", "text"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ChoiceInline]

    fieldsets = [
        (
            "Question Template Information",
            {
                "fields": ["title", "subject", "text"],
            },
        ),
        (
            "Variables (Optional)",
            {
                "fields": ["variables", "validation_rules"],
                "classes": ["collapse"],
                "description": "Define variables for parametric question templates. Use {{variable}} syntax in text. Add validation rules to ensure generated values are valid.",
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
        return qs.select_related("subject")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """Admin interface for Choice model."""

    list_display = ["get_text_preview", "template_preview", "order", "is_correct"]
    list_filter = ["template__subject", "order"]
    search_fields = ["text", "template__text"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = [
        (
            "Choice Information",
            {
                "fields": ["template", "text", "order"],
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

    def get_text_preview(self, obj):
        """Return truncated choice text for list display."""
        try:
            return obj.get_text()[:50]
        except (ValueError, KeyError):
            return "(No text)"

    get_text_preview.short_description = "Choice"

    def template_preview(self, obj):
        """Return truncated question template text."""
        try:
            return obj.template.get_text()[:50]
        except (ValueError, KeyError):
            return "(No template)"

    template_preview.short_description = "Question Template"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("template", "template__subject")
