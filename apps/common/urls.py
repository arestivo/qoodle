"""URL configuration for the common app."""

from django.urls import path

from apps.common import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
