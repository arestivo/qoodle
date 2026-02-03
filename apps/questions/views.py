"""Views for the questions app."""

from typing import Any

from django.contrib import messages
from django.db import models
from django.db.models import Prefetch, QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.questions.forms import ChoiceFormSet, QuestionForm
from apps.questions.models import Choice, Question
from apps.subjects.models import Subject


class QuestionListView(ListView):
    """Display list of questions with optional subject filter."""

    model = Question
    template_name = "questions/question_list.html"
    context_object_name = "questions"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Question]:
        """Return questions, optionally filtered by subject."""
        qs = Question.objects.select_related("subject").prefetch_related(
            Prefetch("choices", queryset=Choice.objects.order_by("order"))
        )

        # Filter by subject if specified
        subject_id = self.request.GET.get("subject")
        include_sub = self.request.GET.get("include_sub") == "on"

        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id)
                if include_sub:
                    # Include questions from subject and all descendants
                    descendants = subject.get_descendants()
                    subject_ids = [subject.id] + [d.id for d in descendants]
                    qs = qs.filter(subject_id__in=subject_ids)
                else:
                    qs = qs.filter(subject=subject)
            except Subject.DoesNotExist:
                pass

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add subjects and filter info to context."""
        context = super().get_context_data(**kwargs)
        context["subjects"] = Subject.objects.all().order_by("name")

        # Add current filter values
        subject_id = self.request.GET.get("subject")
        if subject_id:
            try:
                context["selected_subject"] = Subject.objects.get(pk=subject_id)
            except Subject.DoesNotExist:
                pass

        context["include_sub"] = self.request.GET.get("include_sub") == "on"
        return context


class QuestionCreateView(CreateView):
    """Create a new question with choices."""

    model = Question
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
        context["title"] = "Create Question"
        context["button_text"] = "Create Question"

        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context["choice_formset"] = ChoiceFormSet(instance=self.object)

        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        """Save question and choices with custom handling."""
        # Save the question first
        self.object = form.save()

        # Process choices from POST data
        choices_data = self._extract_choices_from_post()

        if len(choices_data) < 2:
            messages.error(self.request, "You must provide at least 2 choices.")
            return self.render_to_response(self.get_context_data(form=form))

        # Save choices in order
        self._save_choices(choices_data)

        messages.success(
            self.request,
            f"Question created successfully with {len(choices_data)} choices!",
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
                    choice = Choice.objects.get(id=choice_data["id"], question=self.object)
                    choice.text = self._parse_multilingual_text(choice_data["text"])
                    choice.order = i
                    choice.save()
                except Choice.DoesNotExist:
                    # If choice doesn't exist, create it
                    Choice.objects.create(
                        question=self.object,
                        text=self._parse_multilingual_text(choice_data["text"]),
                        order=i,
                    )
            else:
                # Create new
                Choice.objects.create(
                    question=self.object,
                    text=self._parse_multilingual_text(choice_data["text"]),
                    order=i,
                )

    def _parse_multilingual_text(self, text):
        """Parse text using MultilingualTextField logic."""
        from apps.questions.forms import MultilingualTextField

        field = MultilingualTextField()
        return field.to_python(text)


class QuestionUpdateView(UpdateView):
    """Update an existing question and its choices."""

    model = Question
    form_class = QuestionForm
    template_name = "questions/question_form.html"

    def get_success_url(self) -> str:
        """Return preview URL after successful update."""
        return reverse_lazy("questions:preview", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Question"
        context["button_text"] = "Update Question"

        if self.request.POST:
            context["choice_formset"] = ChoiceFormSet(self.request.POST, instance=self.object)
        else:
            context["choice_formset"] = ChoiceFormSet(instance=self.object)

        return context

    def form_valid(self, form: QuestionForm) -> HttpResponse:
        """Save question and choices with custom handling."""
        # Save the question first
        self.object = form.save()

        # Process choices from POST data
        choices_data = self._extract_choices_from_post()

        if len(choices_data) < 2:
            messages.error(self.request, "You must provide at least 2 choices.")
            return self.render_to_response(self.get_context_data(form=form))

        # Save choices in order
        self._save_choices(choices_data)

        messages.success(self.request, "Question updated successfully!")
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
                    choice = Choice.objects.get(id=choice_data["id"], question=self.object)
                    choice.text = self._parse_multilingual_text(choice_data["text"])
                    choice.order = i
                    choice.save()
                except Choice.DoesNotExist:
                    # If choice doesn't exist, create it
                    Choice.objects.create(
                        question=self.object,
                        text=self._parse_multilingual_text(choice_data["text"]),
                        order=i,
                    )
            else:
                # Create new
                Choice.objects.create(
                    question=self.object,
                    text=self._parse_multilingual_text(choice_data["text"]),
                    order=i,
                )

    def _parse_multilingual_text(self, text):
        """Parse text using MultilingualTextField logic."""
        from apps.questions.forms import MultilingualTextField

        field = MultilingualTextField()
        return field.to_python(text)


class QuestionPreviewView(DetailView):
    """Preview question showing all language versions."""

    model = Question
    template_name = "questions/question_preview.html"
    context_object_name = "question"

    def get_queryset(self):
        """Optimize with select_related and prefetch_related."""
        return Question.objects.select_related("subject").prefetch_related(
            Prefetch("choices", queryset=Choice.objects.order_by("order"))
        )

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
                    rendered_texts[lang] = self.object.get_text(
                        language_code=lang, variables=variables
                    )
                except (ValueError, KeyError):
                    rendered_texts[lang] = None

            # Get rendered choice texts for each language
            rendered_choices = []
            for choice in self.object.choices.all():
                choice_texts = {}
                for lang in context["languages"]:
                    try:
                        choice_texts[lang] = choice.get_text(
                            language_code=lang, variables=variables
                        )
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
        except Exception as e:
            # If variable generation fails, include error
            context["preview_instance"] = {
                "seed": seed,
                "error": str(e),
            }

        return context


class QuestionDeleteView(DeleteView):
    """Delete a question and its choices."""

    model = Question
    template_name = "questions/question_confirm_delete.html"
    success_url = reverse_lazy("questions:list")

    def form_valid(self, form: Any) -> HttpResponse:
        """Add success message."""
        question_text = self.object.get_text()[:50]
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f"Question '{question_text}...' and its choices deleted successfully!",
            )
            return response
        except models.ProtectedError:
            messages.error(
                self.request,
                f"Cannot delete question '{question_text}...' due to protected relationships.",
            )
            return self.render_to_response(self.get_context_data())
