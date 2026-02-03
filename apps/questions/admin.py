"""Admin configuration for the questions app."""

from django.contrib import admin

from apps.questions.models import Choice, Question


class ChoiceInline(admin.TabularInline):
    """Inline admin for choices."""

    model = Choice
    extra = 0
    fields = ["text", "order"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model."""

    list_display = ["title", "subject", "choice_count", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["title", "text"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ChoiceInline]

    fieldsets = [
        (
            "Question Information",
            {
                "fields": ["title", "subject", "text"],
            },
        ),
        (
            "Variables (Optional)",
            {
                "fields": ["variables", "validation_rules"],
                "classes": ["collapse"],
                "description": "Define variables for parametric questions. Use {{variable}} syntax in text. Add validation rules to ensure generated values are valid.",
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

    list_display = ["get_text_preview", "question_preview", "order", "is_correct"]
    list_filter = ["question__subject", "order"]
    search_fields = ["text", "question__text"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = [
        (
            "Choice Information",
            {
                "fields": ["question", "text", "order"],
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

    def question_preview(self, obj):
        """Return truncated question text."""
        try:
            return obj.question.get_text()[:50]
        except (ValueError, KeyError):
            return "(No question)"

    question_preview.short_description = "Question"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("question", "question__subject")
