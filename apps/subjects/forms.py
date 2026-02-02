"""Forms for the subjects app."""

from django import forms

from apps.subjects.models import Subject


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects."""

    class Meta:
        model = Subject
        fields = ["name", "parent", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter subject name",
                }
            ),
            "parent": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description",
                }
            ),
        }

    def __init__(self, *args, disable_parent=False, **kwargs):
        """Initialize form and customize parent choices."""
        super().__init__(*args, **kwargs)
        # Exclude current subject from parent choices to prevent circular references
        if self.instance and self.instance.pk:
            descendants = [self.instance.pk] + [d.pk for d in self.instance.get_descendants()]
            self.fields["parent"].queryset = Subject.objects.exclude(pk__in=descendants)

        # Make parent field optional
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "-- Root Level Subject --"

        # Disable parent field if requested (e.g., when creating sub-subject)
        if disable_parent:
            self.fields["parent"].disabled = True
            self.fields["parent"].widget.attrs["class"] += " bg-light"
