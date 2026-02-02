"""Forms for the questions app."""

import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from apps.questions.models import Choice, Question


class MultilingualTextField(forms.CharField):
    """
    Custom field for multilingual text using marker format.

    Format:
        ==en==
        English text
        ==pt==
        Portuguese text

    Or plain text without markers for language-independent content.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("widget", forms.Textarea)
        super().__init__(**kwargs)

    def to_python(self, value):
        """Convert marker format to JSON dict for storage."""
        if not value or value.strip() == "":
            return None

        # Check if text contains language markers
        marker_pattern = r"^==([a-z]{2})==\s*$"
        lines = value.split("\n")

        result = {}
        current_lang = None
        current_text = []

        for line in lines:
            marker_match = re.match(marker_pattern, line.strip())
            if marker_match:
                # Save previous section
                if current_lang is not None:
                    result[current_lang] = "\n".join(current_text).strip()
                # Start new section
                current_lang = marker_match.group(1)
                current_text = []
            else:
                current_text.append(line)

        # Save last section
        if current_lang is not None:
            result[current_lang] = "\n".join(current_text).strip()

        # If no markers found, treat as language-independent
        if not result:
            result = {"none": value.strip()}

        # Validate that we have at least one non-empty value
        if not any(text.strip() for text in result.values()):
            raise ValidationError("Text cannot be empty")

        return result

    def prepare_value(self, value):
        """Convert JSON dict to marker format for display."""
        if not value:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            # If only "none" key exists, show plain text
            if len(value) == 1 and "none" in value:
                return value["none"]

            # Convert to marker format
            parts = []
            for lang_code in sorted(value.keys()):
                if lang_code == "none":
                    continue
                parts.append(f"=={lang_code}==")
                parts.append(value[lang_code])
                parts.append("")  # Empty line between sections

            # Add "none" at the end if it exists
            if "none" in value:
                parts.append("==none==")
                parts.append(value["none"])

            return "\n".join(parts).strip()

        return value


class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions."""

    text = MultilingualTextField(
        label="Question Text",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "==en==\nWhat is 4 + 5?\n\n==pt==\nQuanto é 4 + 5?\n\nOr just enter text without markers for language-independent content.",
            }
        ),
        help_text="Enter text with language markers (e.g., ==en==, ==pt==) or plain text for language-independent content.",
    )

    class Meta:
        model = Question
        fields = ["subject", "text"]
        widgets = {
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }


class ChoiceForm(forms.ModelForm):
    """Form for individual choices."""

    text = MultilingualTextField(
        label="Choice Text",
        widget=forms.Textarea(
            attrs={
                "class": "form-control choice-text",
                "rows": 3,
                "placeholder": "==en==\nNine\n\n==pt==\nNove\n\nOr just: 9",
            }
        ),
        help_text="Enter text with language markers or plain text.",
        required=True,
    )

    class Meta:
        model = Choice
        fields = ["text"]  # Removed order - will be set by position


# Inline formset for editing choices within question form
# Note: We'll handle deletion and ordering manually via JavaScript
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    fields=["text"],  # Order removed - determined by position
    extra=0,
    can_delete=False,  # We'll handle deletion via JavaScript
    min_num=2,
    validate_min=True,
)
