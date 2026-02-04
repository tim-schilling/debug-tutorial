from django.core.paginator import Paginator
from django.template import Library

register = Library()


@register.filter
def is_ellipsis(value):
    """
    Determine if the value is an ellipsis
    """
    return value == Paginator.ELLIPSIS
