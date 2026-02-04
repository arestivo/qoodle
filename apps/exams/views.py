from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .models import Exam, QuestionPool, QuestionPoolTemplate

# Placeholder views - will be implemented in Phase 3


class ExamListView(ListView):
    model = Exam


class ExamDetailView(DetailView):
    model = Exam


class ExamCreateView(CreateView):
    model = Exam


class ExamUpdateView(UpdateView):
    model = Exam


class ExamDeleteView(DeleteView):
    model = Exam


class PoolCreateView(CreateView):
    model = QuestionPool


class PoolUpdateView(UpdateView):
    model = QuestionPool


class PoolDeleteView(DeleteView):
    model = QuestionPool


class PoolReorderView(UpdateView):
    model = QuestionPool


class PoolTemplateAddView(CreateView):
    model = QuestionPoolTemplate


class PoolTemplateDeleteView(DeleteView):
    model = QuestionPoolTemplate
