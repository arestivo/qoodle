"""Forms for the questions app."""

import json
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

    variables_json = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Variable definitions for parametric questions (populated by JavaScript)",
    )

    class Meta:
        model = Question
        fields = ["title", "subject", "text", "variables_json"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Addition of single-digit numbers",
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form and populate variables_json from instance."""
        super().__init__(*args, **kwargs)

        # Populate variables_json field from instance.variables for edit mode
        if self.instance and self.instance.pk and self.instance.variables:
            self.initial["variables_json"] = self.instance.variables

    def clean_variables_json(self):
        """
        Validate variables_json field.

        Returns:
            Dict or empty dict if None

        Raises:
            ValidationError: If malformed JSON
        """
        value = self.cleaned_data.get("variables_json")

        if value is None or value == "":
            return {}

        if isinstance(value, dict):
            return value

        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, dict):
                    raise ValidationError("Variables must be a JSON object/dict")
                return parsed
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")

        raise ValidationError("Variables must be a JSON object")

    def save(self, commit=True):
        """
        Save the question with variables.

        Extracts variables_json from cleaned_data and assigns to instance.variables
        before calling model validation.
        """
        instance = super().save(commit=False)

        # Assign variables from form field to model
        if "variables_json" in self.cleaned_data:
            variables = self.cleaned_data["variables_json"]
            instance.variables = variables if variables else None

        if commit:
            instance.full_clean()  # This calls the model's clean() method
            instance.save()

        return instance


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
