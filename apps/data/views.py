"""Views for the data management app."""

import json
from datetime import date

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from apps.data.services import (
    delete_all_data,
    export_data,
    get_existing_data_counts,
    has_existing_data,
    import_data,
)


class DataIndexView(TemplateView):
    """Data management page with export and import cards."""

    template_name = "data/index.html"


def export_view(request: HttpRequest) -> HttpResponse:
    """Export all application data as a JSON file download."""
    data = export_data()
    content = json.dumps(data, indent=2, ensure_ascii=False)

    filename = f"qoodle-export-{date.today().isoformat()}.json"
    response = HttpResponse(content, content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def import_view(request: HttpRequest) -> HttpResponse:
    """Handle data import via file upload with confirmation flow."""
    if request.method != "POST":
        return redirect("data:index")

    # Check if this is a confirmation POST
    if request.POST.get("confirm") == "true":
        # Retrieve stored data from session
        data = request.session.pop("import_data", None)
        if data is None:
            messages.error(request, "Import session expired. Please upload the file again.")
            return redirect("data:index")

        try:
            with transaction.atomic():
                delete_all_data()
                counts = import_data(data)
        except ValueError as e:
            messages.error(request, f"Import failed: {e}")
            return redirect("data:index")
        except Exception as e:
            messages.error(request, f"Import failed: {e}")
            return redirect("data:index")

        total = sum(counts.values())
        messages.success(request, f"Import complete! {total} records imported.")
        return redirect("data:index")

    # Handle file upload
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        messages.error(request, "No file selected.")
        return redirect("data:index")

    try:
        content = uploaded_file.read().decode("utf-8")
        data = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        messages.error(request, f"Invalid JSON file: {e}")
        return redirect("data:index")

    # Validate version
    if data.get("version") != 1:
        messages.error(
            request,
            f"Unsupported format version: {data.get('version')}. Expected 1.",
        )
        return redirect("data:index")

    # If database has data, show confirmation page
    if has_existing_data():
        request.session["import_data"] = data
        existing_counts = get_existing_data_counts()
        return render(
            request,
            "data/import_confirm.html",
            {"existing_counts": existing_counts},
        )

    # Empty database — import directly
    try:
        with transaction.atomic():
            counts = import_data(data)
    except ValueError as e:
        messages.error(request, f"Import failed: {e}")
        return redirect("data:index")
    except Exception as e:
        messages.error(request, f"Import failed: {e}")
        return redirect("data:index")

    total = sum(counts.values())
    messages.success(request, f"Import complete! {total} records imported.")
    return redirect("data:index")
