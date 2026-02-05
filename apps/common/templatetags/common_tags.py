"""Template tags for common app."""

from django import template

register = template.Library()


@register.filter
def bootstrap_alert_class(message_tag):
    """Convert Django message tags to Bootstrap alert classes.

    Django uses: debug, info, success, warning, error
    Bootstrap uses: primary, secondary, success, danger, warning, info, light, dark

    Usage: {{ message.tags|bootstrap_alert_class }}
    """
    mapping = {
        "debug": "secondary",
        "info": "info",
        "success": "success",
        "warning": "warning",
        "error": "danger",
    }
    return mapping.get(message_tag, "info")

@register.filter
def alert_auto_dismiss(message_tag):
    """Determine if an alert should auto-dismiss.
    
    Success and info messages auto-dismiss after 5 seconds.
    Error, warning, and debug messages require manual dismissal.
    
    Usage: {% if message.tags|alert_auto_dismiss %}data-bs-autohide="true"{% endif %}
    """
    auto_dismiss_tags = {"success", "info"}
    return message_tag in auto_dismiss_tags
