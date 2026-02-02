"""Template tags for the questions app."""

import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.

    Usage: {{ mydict|get_item:key }}
    """
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""


@register.filter(name="markdown")
def markdown_filter(text):
    """
    Convert markdown text to HTML.

    Usage: {{ text|markdown }}
    """
    if not text:
        return ""

    # Configure markdown with common extensions
    html = md.markdown(
        text,
        extensions=[
            "nl2br",  # Convert newlines to <br>
            "fenced_code",  # Support ```code blocks```
            "tables",  # Support tables
            "sane_lists",  # Better list handling
        ],
    )
    return mark_safe(html)
