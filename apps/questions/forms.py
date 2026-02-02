"""Forms for the questions app."""

from django import forms
from django.forms import inlineformset_factory

from apps.questions.models import Choice, Question


class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions."""

    class Meta:
        model = Question
        fields = ["subject", "text"]
        widgets = {
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": 'Enter question text as JSON, e.g., {"none": "What is 4 + 5?", "en": "What is 4 + 5?", "pt": "Quanto é 4 + 5?"}',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.fields["text"].help_text = 'Enter question text as JSON with language codes. Use "none" for language-independent text. Example: {"none": "4 + 5 = ?", "en": "What is 4 + 5?"}'


class ChoiceForm(forms.ModelForm):
    """Form for individual choices."""

    class Meta:
        model = Choice
        fields = ["text", "order"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": 'Enter choice text as JSON, e.g., {"none": "9", "en": "Nine", "pt": "Nove"}',
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
        }


# Inline formset for editing choices within question form
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    fields=["text", "order"],
    extra=2,
    can_delete=True,
    min_num=2,
    validate_min=True,
)
