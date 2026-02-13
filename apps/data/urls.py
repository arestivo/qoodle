"""URL configuration for the data app."""

from django.urls import path

from apps.data import views

app_name = "data"

urlpatterns = [
    path("", views.DataIndexView.as_view(), name="index"),
    path("export/", views.export_view, name="export"),
    path("import/", views.import_view, name="import"),
]
