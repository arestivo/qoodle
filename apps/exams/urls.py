from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    # Exam CRUD
    path("", views.ExamListView.as_view(), name="list"),
    path("create/", views.ExamCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.ExamDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.ExamUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.ExamDeleteView.as_view(), name="delete"),
    # Pool Management
    path(
        "<uuid:exam_pk>/pools/add/",
        views.PoolCreateView.as_view(),
        name="pool_create",
    ),
    path(
        "<uuid:exam_pk>/pools/<uuid:pk>/delete/",
        views.PoolDeleteView.as_view(),
        name="pool_delete",
    ),
    path(
        "<uuid:exam_pk>/pools/<uuid:pk>/reorder/",
        views.PoolReorderView.as_view(),
        name="pool_reorder",
    ),
    # Template Selection for Pool
    path(
        "<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/add/",
        views.PoolTemplateAddView.as_view(),
        name="pool_template_add",
    ),
    path(
        "<uuid:exam_pk>/pools/<uuid:pool_pk>/templates/<uuid:pk>/delete/",
        views.PoolTemplateDeleteView.as_view(),
        name="pool_template_delete",
    ),
    # Moodle Export
    path(
        "<uuid:pk>/export/",
        views.ExamExportView.as_view(),
        name="export",
    ),
    # Pool Grade Update
    path(
        "<uuid:exam_pk>/pools/<uuid:pk>/grade/",
        views.PoolUpdateGradeView.as_view(),
        name="pool_update_grade",
    ),
]
