"""Views for the subjects app."""

from typing import Any

from django.contrib import messages
from django.db import models
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.subjects.forms import SubjectForm
from apps.subjects.models import Subject


class SubjectListView(ListView):
    """Display hierarchical list of all subjects."""

    model = Subject
    template_name = "subjects/subject_list.html"
    context_object_name = "subjects"

    def get_queryset(self) -> QuerySet[Subject]:
        """Return all subjects with their parents and children prefetched."""
        return Subject.objects.select_related("parent").prefetch_related("children")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add tree structure to context."""
        context = super().get_context_data(**kwargs)
        # Get root subjects (those without a parent)
        context["root_subjects"] = self.get_queryset().filter(parent__isnull=True)
        return context


class SubjectCreateView(CreateView):
    """Create a new subject."""

    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subjects:list")

    def get_initial(self) -> dict[str, Any]:
        """Set initial parent if provided in GET parameter."""
        initial = super().get_initial()
        parent_pk = self.request.GET.get("parent")
        if parent_pk:
            try:
                parent = Subject.objects.get(pk=parent_pk)
                initial["parent"] = parent
            except Subject.DoesNotExist:
                pass
        return initial

    def get_form_kwargs(self) -> dict[str, Any]:
        """Add disable_parent flag if parent is pre-selected."""
        kwargs = super().get_form_kwargs()
        parent_pk = self.request.GET.get("parent")
        if parent_pk:
            kwargs["disable_parent"] = True
        return kwargs

    def form_valid(self, form: SubjectForm) -> HttpResponse:
        """Add success message on valid form submission."""
        messages.success(self.request, f"Subject '{form.instance.name}' created successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        parent_pk = self.request.GET.get("parent")
        if parent_pk:
            try:
                parent = Subject.objects.get(pk=parent_pk)
                context["title"] = f"Create Sub-subject under {parent.name}"
            except Subject.DoesNotExist:
                context["title"] = "Create Subject"
        else:
            context["title"] = "Create Subject"
        context["button_text"] = "Create Subject"
        return context


class SubjectUpdateView(UpdateView):
    """Update an existing subject."""

    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subjects:list")

    def form_valid(self, form: SubjectForm) -> HttpResponse:
        """Add success message on valid form submission."""
        messages.success(self.request, f"Subject '{form.instance.name}' updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Subject: {self.object.name}"
        context["button_text"] = "Update Subject"
        return context


class SubjectDeleteView(DeleteView):
    """Delete a subject."""

    model = Subject
    template_name = "subjects/subject_confirm_delete.html"
    success_url = reverse_lazy("subjects:list")

    def form_valid(self, form: Any) -> HttpResponse:
        """Add success message and handle protected deletion."""
        subject_name = self.object.name
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"Subject '{subject_name}' deleted successfully!")
            return response
        except models.ProtectedError:
            messages.error(
                self.request,
                f"Cannot delete '{subject_name}' because it has child subjects. Please delete or move the child subjects first.",
            )
            return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add children count to context."""
        context = super().get_context_data(**kwargs)
        context["children_count"] = self.object.children.count()
        return context
