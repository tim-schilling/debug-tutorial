from datetime import timedelta

from django.core.paginator import Paginator
from django.template import Library
from django.utils import timezone

from project.newsletter.models import Post

register = Library()


@register.filter
def is_ellipsis(value):
    """
    Determine if the value is an ellipsis
    """
    return value == Paginator.ELLIPSIS


@register.inclusion_tag("inclusion_tags/nice_datetime.html")
def nice_datetime(post: Post, is_unread: bool):
    """
    Format the datetime in the locale the user prefers with styling.
    """
    now = timezone.now()
    week_ago = timezone.now() - timedelta(days=7)
    timestamp = post.created
    is_recent = week_ago <= timestamp <= now
    return {
        "is_unread": is_unread,
        "is_recent": is_recent,
        "timestamp": timestamp,
    }
