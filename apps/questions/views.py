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
        qs = Question.objects.select_related("subject").prefetch_related(Prefetch("choices", queryset=Choice.objects.order_by("order")))

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
        """Save question and choices together."""
        context = self.get_context_data()
        choice_formset = context["choice_formset"]

        if choice_formset.is_valid():
            self.object = form.save()
            choice_formset.instance = self.object
            choice_formset.save()
            messages.success(
                self.request,
                f"Question created successfully with {self.object.choice_count} choices!",
            )
            return super().form_valid(form)
        else:
            return self.render_to_response(context)


class QuestionUpdateView(UpdateView):
    """Update an existing question and its choices."""

    model = Question
    form_class = QuestionForm
    template_name = "questions/question_form.html"
    success_url = reverse_lazy("questions:list")

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
        """Save question and choices together."""
        context = self.get_context_data()
        choice_formset = context["choice_formset"]

        if choice_formset.is_valid():
            self.object = form.save()
            choice_formset.instance = self.object
            choice_formset.save()
            messages.success(self.request, "Question updated successfully!")
            return super().form_valid(form)
        else:
            return self.render_to_response(context)


class QuestionPreviewView(DetailView):
    """Preview question showing all language versions."""

    model = Question
    template_name = "questions/question_preview.html"
    context_object_name = "question"

    def get_queryset(self):
        """Optimize with select_related and prefetch_related."""
        return Question.objects.select_related("subject").prefetch_related(Prefetch("choices", queryset=Choice.objects.order_by("order")))

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
