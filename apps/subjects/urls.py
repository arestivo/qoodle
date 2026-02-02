"""URL configuration for the subjects app."""

from django.urls import path

from apps.subjects import views

app_name = "subjects"

urlpatterns = [
    path("", views.SubjectListView.as_view(), name="list"),
    path("create/", views.SubjectCreateView.as_view(), name="create"),
    path("<uuid:pk>/edit/", views.SubjectUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.SubjectDeleteView.as_view(), name="delete"),
]
