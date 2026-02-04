from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import TemplateView

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


class PoolTemplateAddView(TemplateView):
    """Add question templates to a pool in bulk."""

    template_name = "exams/pool_template_add.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])
        exam = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])

        context["exam"] = exam
        context["pool"] = pool

        # Filter available templates - exclude those already used in ANY question in this exam
        from apps.questions.models import QuestionTemplate
        from apps.subjects.models import Subject

        # Get all template IDs already used in any pool in this exam
        existing_template_ids = QuestionPoolTemplate.objects.filter(pool__exam=exam).values_list("template_id", flat=True)

        available_templates = QuestionTemplate.objects.exclude(id__in=existing_template_ids).select_related("subject")

        # Filter by subject if provided
        subject_id = self.request.GET.get("subject")
        if subject_id:
            available_templates = available_templates.filter(subject_id=subject_id)
            context["selected_subject"] = subject_id

        context["available_templates"] = available_templates
        context["subjects"] = Subject.objects.all().order_by("name")

        return context

    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])

        # Get selected template IDs from checkboxes
        template_ids = request.POST.getlist("templates")

        if not template_ids:
            # No templates selected, redirect back with error message
            return redirect(reverse("exams:pool_template_add", kwargs={"exam_pk": self.kwargs["exam_pk"], "pool_pk": self.kwargs["pool_pk"]}))

        # Get default number of versions
        default_versions = int(request.POST.get("default_versions", 5))

        # Create pool template entries for each selected template
        from apps.questions.models import QuestionTemplate

        for template_id in template_ids:
            template = QuestionTemplate.objects.get(pk=template_id)

            # If template has no variables, use 1 version, otherwise use default
            num_versions = 1 if not template.variables else default_versions

            QuestionPoolTemplate.objects.create(pool=pool, template=template, number_of_versions=num_versions)

        return redirect("exams:detail", pk=self.kwargs["exam_pk"])


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
