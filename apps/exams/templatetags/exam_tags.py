"""Template tags for exam views."""

from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """Get a value from a dictionary using a key.

    Usage: {{ my_dict|dict_get:my_key }}
    """
    if dictionary is None:
        return None
    # Convert UUID to string for lookup
    key_str = str(key)
    return dictionary.get(key_str)
