"""Views for the questions app."""

from typing import Any

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.questions.forms import ChoiceFormSet, QuestionForm
from apps.questions.models import Choice, QuestionTemplate
from apps.subjects.models import Subject


class QuestionListView(ListView):
    """Display list of question templates with optional subject filter."""

    model = QuestionTemplate
    template_name = "questions/question_list.html"
    context_object_name = "questions"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[QuestionTemplate]:
        """Return question templates, optionally filtered by subject."""
        qs = QuestionTemplate.objects.select_related("subject").prefetch_related(Prefetch("choices", queryset=Choice.objects.order_by("order")))

        # Filter by subject if specified
        subject_id = self.request.GET.get("subject")
        include_sub = self.request.GET.get("include_sub") == "on"

        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id)
                if include_sub:
                    # Include question templates from subject and all descendants
                    descendants = subject.get_descendants()
                    subject_ids = [subject.id] + [d.id for d in descendants]
                    qs = qs.filter(subject_id__in=subject_ids)
                else:
                    qs = qs.filter(subject=subject)
            except Subject.DoesNotExist:
                pass

        # Filter by state if specified
        state = self.request.GET.get("state")
        if state:
            qs = qs.filter(state=state)

        return qs.order_by("title")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add subjects and filter info to context."""
        context = super().get_context_data(**kwargs)

        # Get all subjects and sort by full path
        all_subjects = Subject.objects.select_related("parent").all()
        subjects_with_paths = [(subject, subject.get_full_path()) for subject in all_subjects]
        # Sort alphabetically by full path
        subjects_with_paths.sort(key=lambda x: x[1])
        context["subjects"] = [subject for subject, _ in subjects_with_paths]

        # Add current filter values
        subject_id = self.request.GET.get("subject")
        if subject_id:
            try:
                context["selected_subject"] = Subject.objects.get(pk=subject_id)
            except Subject.DoesNotExist:
                pass

        context["include_sub"] = self.request.GET.get("include_sub") == "on"
        context["selected_state"] = self.request.GET.get("state", "")
        return context


class QuestionCreateView(CreateView):
    """Create a new question template with choices."""

    model = QuestionTemplate
    form_class = QuestionForm
    template_name = "questions/question_form.html"
    success_url = reverse_lazy("questions:list")

    def get_initial(self) -> dict[str, Any]:
        """Set initial subject if provided in GET parameter."""
        initial = super().get_initial()
        subject_pk = self.request.GET.get("subject")
        if subject_pk:
            try:
                subject = Subject.objects.get(pk=subject_pk)
                initial["subject"] = subject
            except Subject.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Template"
        context["button_text"] = "Create Template"

        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context["choice_formset"] = ChoiceFormSet(instance=self.object)

        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        """Save question and choices with custom handling."""
        # Save the question first
        try:
            self.object = form.save()
        except ValidationError:
            # ValidationError was already added to form errors in form.save()
            return self.form_invalid(form)

        # Process choices from POST data
        choices_data = self._extract_choices_from_post()

        if len(choices_data) < 2:
            messages.error(self.request, "You must provide at least 2 choices.")
            return self.render_to_response(self.get_context_data(form=form))

        # Save choices in order
        self._save_choices(choices_data)

        messages.success(
            self.request,
            f"Question template created successfully with {len(choices_data)} choices!",
        )
        return HttpResponse(status=302, headers={"Location": str(self.success_url)})

    def _extract_choices_from_post(self):
        """Extract choice data from POST in order."""
        choices = []
        i = 0
        while f"choices-{i}-text" in self.request.POST:
            text = self.request.POST.get(f"choices-{i}-text")
            choice_id = self.request.POST.get(f"choices-{i}-id")

            if text and text.strip():  # Only include non-empty choices
                choices.append(
                    {
                        "id": choice_id if choice_id else None,
                        "text": text,
                        "order": len(choices),  # Order based on position
                    }
                )
            i += 1
        return choices

    def _save_choices(self, choices_data):
        """Save choices and delete any not included."""
        # Get existing choice IDs that should be kept (filter out None and empty strings)
        submitted_ids = [c["id"] for c in choices_data if c["id"]]

        # Delete choices not in submission
        if submitted_ids:
            self.object.choices.exclude(id__in=submitted_ids).delete()
        else:
            # If no submitted IDs, delete all existing choices
            self.object.choices.all().delete()

        # Create or update choices in order
        for i, choice_data in enumerate(choices_data):
            if choice_data["id"]:
                # Update existing - fetch instance and update
                try:
                    choice = Choice.objects.get(id=choice_data["id"], template=self.object)
                    choice.text = self._parse_multilingual_text(choice_data["text"])
                    choice.order = i
                    choice.save()
                except Choice.DoesNotExist:
                    # If choice doesn't exist, create it
                    Choice.objects.create(
                        template=self.object,
                        text=self._parse_multilingual_text(choice_data["text"]),
                        order=i,
                    )
            else:
                # Create new
                Choice.objects.create(
                    template=self.object,
                    text=self._parse_multilingual_text(choice_data["text"]),
                    order=i,
                )

    def _parse_multilingual_text(self, text):
        """Parse text using MultilingualTextField logic."""
        from apps.questions.forms import MultilingualTextField

        field = MultilingualTextField()
        return field.to_python(text)


class QuestionUpdateView(UpdateView):
    """Update an existing question template and its choices."""

    model = QuestionTemplate
    form_class = QuestionForm
    template_name = "questions/question_form.html"

    def get_success_url(self) -> str:
        """Return preview URL after successful update."""
        return reverse_lazy("questions:preview", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Template"
        context["button_text"] = "Update Template"

        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context["choice_formset"] = ChoiceFormSet(instance=self.object)

        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        """Save question and choices with custom handling."""
        # Save the question first
        try:
            self.object = form.save()
        except ValidationError:
            # ValidationError was already added to form errors in form.save()
            return self.form_invalid(form)

        # Process choices from POST data
        choices_data = self._extract_choices_from_post()

        if len(choices_data) < 2:
            messages.error(self.request, "You must provide at least 2 choices.")
            return self.render_to_response(self.get_context_data(form=form))

        # Save choices in order
        self._save_choices(choices_data)

        messages.success(self.request, "Question template updated successfully!")
        return HttpResponse(status=302, headers={"Location": str(self.get_success_url())})

    def _extract_choices_from_post(self):
        """Extract choice data from POST in order."""
        choices = []
        i = 0
        while f"choices-{i}-text" in self.request.POST:
            text = self.request.POST.get(f"choices-{i}-text")
            choice_id = self.request.POST.get(f"choices-{i}-id")

            if text and text.strip():  # Only include non-empty choices
                choices.append(
                    {
                        "id": choice_id if choice_id else None,
                        "text": text,
                        "order": len(choices),  # Order based on position
                    }
                )
            i += 1
        return choices

    def _save_choices(self, choices_data):
        """Save choices and delete any not included."""
        # Get existing choice IDs that should be kept (filter out None and empty strings)
        submitted_ids = [c["id"] for c in choices_data if c["id"]]

        # Delete choices not in submission
        if submitted_ids:
            self.object.choices.exclude(id__in=submitted_ids).delete()
        else:
            # If no submitted IDs, delete all existing choices
            self.object.choices.all().delete()

        # Create or update choices in order
        for i, choice_data in enumerate(choices_data):
            if choice_data["id"]:
                # Update existing - fetch instance and update
                try:
                    choice = Choice.objects.get(id=choice_data["id"], template=self.object)
                    choice.text = self._parse_multilingual_text(choice_data["text"])
                    choice.order = i
                    choice.save()
                except Choice.DoesNotExist:
                    # If choice doesn't exist, create it
                    Choice.objects.create(
                        template=self.object,
                        text=self._parse_multilingual_text(choice_data["text"]),
                        order=i,
                    )
            else:
                # Create new
                Choice.objects.create(
                    template=self.object,
                    text=self._parse_multilingual_text(choice_data["text"]),
                    order=i,
                )

    def _parse_multilingual_text(self, text):
        """Parse text using MultilingualTextField logic."""
        from apps.questions.forms import MultilingualTextField

        field = MultilingualTextField()
        return field.to_python(text)


class QuestionPreviewView(DetailView):
    """Preview question template showing all language versions."""

    model = QuestionTemplate
    template_name = "questions/question_preview.html"
    context_object_name = "question"

    def get_queryset(self):
        """Optimize with select_related and prefetch_related."""
        return QuestionTemplate.objects.select_related("subject").prefetch_related(Prefetch("choices", queryset=Choice.objects.order_by("order")))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add all available languages to context."""
        context = super().get_context_data(**kwargs)

        # Collect all unique languages from question and choices
        languages = set()
        languages.update(self.object.available_languages())
        for choice in self.object.choices.all():
            languages.update(choice.text.keys() if choice.text else set())

        # Only show "none" if there are no other language-specific versions
        if len(languages) > 1 and "none" in languages:
            languages.discard("none")

        context["languages"] = sorted(languages)

        # Check for missing translations per language
        # For each specific language (not 'none'), check if all parts have that language
        translation_issues = {}
        for lang in context["languages"]:
            if lang == "none":
                continue

            issues = []

            # Check if question has this language
            question_langs = set(self.object.text.keys()) if self.object.text else set()
            has_question_lang = lang in question_langs or "none" in question_langs

            if not has_question_lang:
                issues.append("Question text missing")

            # Check each choice
            for choice in self.object.choices.all():
                choice_langs = set(choice.text.keys()) if choice.text else set()
                has_choice_lang = lang in choice_langs or "none" in choice_langs

                if not has_choice_lang:
                    issues.append(f"Choice {choice.order + 1} missing")

            if issues:
                translation_issues[lang] = issues

        context["translation_issues"] = translation_issues

        # Generate a single random preview instance
        import random

        seed = random.randint(0, 999999)

        try:
            # Generate variables for this instance (empty dict if no variables)
            variables = self.object.generate_variables(seed=seed)

            # Get rendered question text for each language
            rendered_texts = {}
            for lang in context["languages"]:
                try:
                    rendered_texts[lang] = self.object.get_text(language_code=lang, variables=variables)
                except (ValueError, KeyError):
                    rendered_texts[lang] = None

            # Get rendered choice texts for each language
            rendered_choices = []
            for choice in self.object.choices.all():
                choice_texts = {}
                for lang in context["languages"]:
                    try:
                        choice_texts[lang] = choice.get_text(language_code=lang, variables=variables)
                    except (ValueError, KeyError):
                        choice_texts[lang] = None
                rendered_choices.append(
                    {
                        "id": choice.id,
                        "is_correct": choice.is_correct,
                        "order": choice.order,
                        "texts": choice_texts,
                    }
                )

            context["preview_instance"] = {
                "seed": seed,
                "variables": variables,
                "question_texts": rendered_texts,
                "choices": rendered_choices,
            }
        except ValidationError as e:
            # Validation rules could not be satisfied after max attempts
            context["preview_instance"] = {
                "seed": seed,
                "validation_error": True,
                "error": str(e),
                "error_type": "validation_rules",
            }
        except Exception as e:
            # Other errors (e.g., invalid variable expressions)
            context["preview_instance"] = {
                "seed": seed,
                "validation_error": False,
                "error": str(e),
                "error_type": "general",
            }

        return context


class QuestionDeleteView(DeleteView):
    """Delete a question template and its choices."""

    model = QuestionTemplate
    template_name = "questions/question_confirm_delete.html"
    success_url = reverse_lazy("questions:list")

    def form_valid(self, form: Any) -> HttpResponse:
        """Add success message."""
        question_text = self.object.get_text()[:50]
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f"Question template '{question_text}...' and its choices deleted successfully!",
            )
            return response
        except models.ProtectedError:
            messages.error(
                self.request,
                f"Cannot delete question template '{question_text}...' due to protected relationships.",
            )
            return self.render_to_response(self.get_context_data())


@require_POST
def bulk_move_templates(request: HttpRequest) -> HttpResponse:
    """Move multiple templates to a different subject."""
    template_ids = request.POST.getlist("template_ids")
    subject_id = request.POST.get("subject_id")

    if not template_ids:
        messages.warning(request, "Please select at least one template.")
        return HttpResponseRedirect(reverse("questions:list"))

    if not subject_id:
        messages.warning(request, "Please select a destination subject.")
        return HttpResponseRedirect(reverse("questions:list"))

    try:
        subject = Subject.objects.get(pk=subject_id)
    except Subject.DoesNotExist:
        messages.error(request, "Selected subject does not exist.")
        return HttpResponseRedirect(reverse("questions:list"))

    # Update templates
    updated_count = QuestionTemplate.objects.filter(pk__in=template_ids).update(subject=subject)

    if updated_count > 0:
        messages.success(request, f"{updated_count} template(s) moved to {subject.name}.")
    else:
        messages.warning(request, "No templates were moved.")

    return HttpResponseRedirect(reverse("questions:list"))


@require_POST
def bulk_delete_templates(request: HttpRequest) -> HttpResponse:
    """Delete multiple templates at once."""
    template_ids = request.POST.getlist("template_ids")

    if not template_ids:
        messages.warning(request, "Please select at least one template.")
        return HttpResponseRedirect(reverse("questions:list"))

    # Delete templates (choices are deleted via CASCADE)
    deleted_count, _ = QuestionTemplate.objects.filter(pk__in=template_ids).delete()

    if deleted_count > 0:
        messages.success(request, f"{deleted_count} template(s) deleted.")
    else:
        messages.warning(request, "No templates were deleted.")

    return HttpResponseRedirect(reverse("questions:list"))
