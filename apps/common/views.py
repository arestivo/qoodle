"""Views for the common app."""

from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Home page view."""

    template_name = "common/home.html"

    def get_context_data(self, **kwargs):
        """Add context data to the template."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Welcome to Qoodle"
        return context
