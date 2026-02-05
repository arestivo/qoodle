"""Forms for exam management.

This module defines forms for creating and editing exams and question pool templates:
- ExamForm: Form for exam creation and editing
- QuestionPoolTemplateFormSet: Formset for bulk adding templates to pools
"""

from django import forms
from django.forms import modelformset_factory

from .models import Exam, QuestionPool, QuestionPoolTemplate


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["title", "date", "description", "grading_mode"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Midterm Exam 2026"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional exam description",
                }
            ),
            "grading_mode": forms.RadioSelect(),
        }


class QuestionPoolForm(forms.ModelForm):
    class Meta:
        model = QuestionPool
        fields = []  # Order is set automatically, no user-editable fields


class PoolGradeForm(forms.ModelForm):
    """Form for updating pool default grade."""
    
    class Meta:
        model = QuestionPool
        fields = ["default_grade"]
        widgets = {
            "default_grade": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.1",
                "min": "0.1"
            })
        }


QuestionPoolTemplateFormSet = modelformset_factory(
    QuestionPoolTemplate,
    fields=["template", "number_of_versions"],
    extra=3,
    can_delete=True,
    widgets={
        "template": forms.Select(attrs={"class": "form-select"}),
        "number_of_versions": forms.NumberInput(attrs={"class": "form-control", "min": 1, "value": 1}),
    },
)
