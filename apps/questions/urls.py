"""URL configuration for the questions app."""

from django.urls import path

from apps.questions import views

app_name = "questions"

urlpatterns = [
    path("", views.QuestionListView.as_view(), name="list"),
    path("create/", views.QuestionCreateView.as_view(), name="create"),
    path("bulk-move/", views.bulk_move_templates, name="bulk_move"),
    path("bulk-delete/", views.bulk_delete_templates, name="bulk_delete"),
    path("<uuid:pk>/", views.QuestionPreviewView.as_view(), name="preview"),
    path("<uuid:pk>/edit/", views.QuestionUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.QuestionDeleteView.as_view(), name="delete"),
]
