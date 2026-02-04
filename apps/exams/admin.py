"""Admin configuration for exam management.

This module registers Exam and QuestionPool models in the Django admin interface
with inline editing for pools and pool templates.
"""

from django.contrib import admin

from .models import Exam, QuestionPool, QuestionPoolTemplate


class QuestionPoolInline(admin.TabularInline):
    model = QuestionPool
    extra = 1
    fields = ["order"]


class QuestionPoolTemplateInline(admin.TabularInline):
    model = QuestionPoolTemplate
    extra = 1
    fields = ["template", "number_of_versions"]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "pool_count", "created_at"]
    search_fields = ["title", "description"]
    list_filter = ["date", "created_at"]
    inlines = [QuestionPoolInline]

    def pool_count(self, obj):
        return obj.pools.count()

    pool_count.short_description = "Pools"


@admin.register(QuestionPool)
class QuestionPoolAdmin(admin.ModelAdmin):
    list_display = ["__str__", "exam", "order", "template_count"]
    list_filter = ["exam"]
    inlines = [QuestionPoolTemplateInline]

    def template_count(self, obj):
        return obj.pool_templates.count()

    template_count.short_description = "Templates"


@admin.register(QuestionPoolTemplate)
class QuestionPoolTemplateAdmin(admin.ModelAdmin):
    list_display = ["pool", "template", "number_of_versions"]
    list_filter = ["pool__exam"]
