from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ExamForm, QuestionPoolForm
from .models import Exam, QuestionPool, QuestionPoolTemplate


class ExamListView(ListView):
    model = Exam
    template_name = "exams/exam_list.html"
    context_object_name = "exams"
    paginate_by = 20


class ExamDetailView(DetailView):
    model = Exam
    template_name = "exams/exam_detail.html"
    context_object_name = "exam"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch pools with their templates for efficiency
        context["pools"] = self.object.pools.prefetch_related("pool_templates__template").all()
        return context


class ExamCreateView(CreateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.object.pk})


class ExamUpdateView(UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.object.pk})


class ExamDeleteView(DeleteView):
    model = Exam
    template_name = "exams/exam_confirm_delete.html"
    success_url = reverse_lazy("exams:list")


class PoolCreateView(CreateView):
    model = QuestionPool
    form_class = QuestionPoolForm
    template_name = "exams/pool_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        return context

    def form_valid(self, form):
        exam = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        form.instance.exam = exam
        # Set order to max+1
        max_order = exam.pools.aggregate(models.Max("order"))["order__max"] or 0
        form.instance.order = max_order + 1
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolUpdateView(UpdateView):
    model = QuestionPool
    form_class = QuestionPoolForm
    template_name = "exams/pool_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        return context

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolDeleteView(DeleteView):
    model = QuestionPool
    template_name = "exams/pool_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        return context

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolReorderView(UpdateView):
    """Placeholder for pool reordering - can be implemented later."""

    model = QuestionPool

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolTemplateAddView(CreateView):
    """Add a question template to a pool."""

    model = QuestionPoolTemplate
    fields = ["template", "number_of_versions"]
    template_name = "exams/pool_template_add.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])
        exam = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])

        context["exam"] = exam
        context["pool"] = pool

        # Filter available templates - exclude those already in this pool
        from apps.questions.models import QuestionTemplate
        from apps.subjects.models import Subject

        existing_template_ids = pool.pool_templates.values_list("template_id", flat=True)
        available_templates = QuestionTemplate.objects.exclude(
            id__in=existing_template_ids
        ).select_related("subject")

        # Filter by subject if provided
        subject_id = self.request.GET.get("subject")
        if subject_id:
            available_templates = available_templates.filter(subject_id=subject_id)
            context["selected_subject"] = subject_id

        context["available_templates"] = available_templates
        context["subjects"] = Subject.objects.all().order_by("name")

        return context

    def form_valid(self, form):
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])
        form.instance.pool = pool
        
        # If template has no variables, set number_of_versions to 1
        template = form.cleaned_data["template"]
        if not template.variables:  # Empty string or None
            form.instance.number_of_versions = 1
        
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes
        form.fields["template"].widget.attrs.update({"class": "form-select"})
        form.fields["number_of_versions"].widget.attrs.update({"class": "form-control", "min": 1, "value": 5})

        # Filter templates - apply subject filter if provided
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])
        from apps.questions.models import QuestionTemplate

        existing_template_ids = pool.pool_templates.values_list("template_id", flat=True)
        queryset = QuestionTemplate.objects.exclude(
            id__in=existing_template_ids
        ).select_related("subject")

        # Apply subject filter from GET parameter
        subject_id = self.request.GET.get("subject")
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        form.fields["template"].queryset = queryset

        return form

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolTemplateDeleteView(DeleteView):
    """Remove a question template from a pool."""

    model = QuestionPoolTemplate
    template_name = "exams/pool_template_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        context["pool"] = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])
        return context

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})
