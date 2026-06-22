"""Views for exam management.

This module provides CBVs for CRUD operations on exams and question pools:
- Exam CRUD: List, Create, Detail, Update, Delete
- Pool management: Create, Delete, Reorder
- Pool template management: Add templates via formset, Delete templates
- Moodle export: Generate and download XML files
"""

from decimal import Decimal

from django.contrib import messages
from django.db import models, transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import TemplateView

from .forms import ExamForm, PoolGradeForm
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
        pools = self.object.pools.prefetch_related("pool_templates__template__choices").all()
        context["pools"] = pools
        context["total_points"] = self.object.pools.aggregate(total=Sum("default_grade"))["total"] or Decimal("0.00")
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


class PoolCreateView(View):
    """Create a new question pool without a form - just creates it directly."""

    def get(self, request, *args, **kwargs):
        """Create a new pool and redirect to exam detail."""
        exam = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])

        # Set order to max+1
        max_order = exam.pools.aggregate(models.Max("order"))["order__max"] or 0

        # Create the pool
        QuestionPool.objects.create(exam=exam, order=max_order + 1)

        return redirect("exams:detail", pk=exam.pk)


class PoolDeleteView(DeleteView):
    model = QuestionPool
    template_name = "exams/pool_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        return context

    def form_valid(self, form):
        """Delete the pool and renumber remaining pools sequentially."""
        exam = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])

        # Delete the pool
        response = super().form_valid(form)

        # Renumber all remaining pools sequentially (1, 2, 3, ...)
        for index, pool in enumerate(exam.pools.order_by("order"), start=1):
            pool.order = index
            pool.save()

        return response

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})


class PoolReorderView(View):
    """Reorder a pool up or down within an exam."""

    def post(self, request, exam_pk, pk):
        pool = get_object_or_404(QuestionPool, pk=pk, exam_id=exam_pk)
        exam = pool.exam
        direction = request.POST.get("direction")

        if direction == "up":
            other_pool = exam.pools.filter(order__lt=pool.order).order_by("-order").first()
        elif direction == "down":
            other_pool = exam.pools.filter(order__gt=pool.order).order_by("order").first()
        else:
            other_pool = None

        if other_pool:
            # Use a temporary negative value to avoid constraint violation
            pool_order = pool.order
            other_order = other_pool.order

            with transaction.atomic():
                pool.order = 0
                pool.save()
                other_pool.order = pool_order
                other_pool.save()
                pool.order = other_order
                pool.save()

        return redirect("exams:detail", pk=exam_pk)


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

        available_templates = QuestionTemplate.objects.exclude(id__in=existing_template_ids).filter(state="reviewed").select_related("subject").order_by("title")

        # Filter by subject if provided
        subject_id = self.request.GET.get("subject")
        if subject_id:
            available_templates = available_templates.filter(subject_id=subject_id)
            context["selected_subject"] = subject_id

        context["available_templates"] = available_templates

        # Get all subjects and sort by full path (same as questions list)
        all_subjects = Subject.objects.select_related("parent").all()
        subjects_with_paths = [(subject, subject.get_full_path()) for subject in all_subjects]
        subjects_with_paths.sort(key=lambda x: x[1])
        context["subjects"] = [subject for subject, _ in subjects_with_paths]

        return context

    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(QuestionPool, pk=self.kwargs["pool_pk"])

        # Get selected template IDs from checkboxes
        template_ids = request.POST.getlist("templates")

        if not template_ids:
            # No templates selected, redirect back with error message
            return redirect(
                reverse(
                    "exams:pool_template_add",
                    kwargs={"exam_pk": self.kwargs["exam_pk"], "pool_pk": self.kwargs["pool_pk"]},
                )
            )

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


class ExamExportView(View):
    """Export exam to Moodle XML format."""

    def post(self, request, pk):
        from .moodle_export import generate_moodle_xml

        exam = get_object_or_404(Exam, pk=pk)
        language = request.POST.get("language", "en")

        try:
            xml_content = generate_moodle_xml(exam, language)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("exams:detail", pk=exam.pk)

        # Return XML file download
        response = HttpResponse(xml_content, content_type="application/xml")
        filename = f"{exam.title.replace(' ', '_')}_{language}.xml"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class PoolUpdateGradeView(UpdateView):
    """Update the default grade for a question pool."""

    model = QuestionPool
    form_class = PoolGradeForm
    template_name = "exams/pool_grade_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, pk=self.kwargs["exam_pk"])
        return context

    def get_success_url(self):
        return reverse("exams:detail", kwargs={"pk": self.kwargs["exam_pk"]})

    def form_valid(self, form):
        messages.success(self.request, f"Pool {self.object.order} grade updated to {form.cleaned_data['default_grade']} points")
        return super().form_valid(form)
