"""
This file contains create/update/writing operations.
"""
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from martor.views import User

from project.newsletter.models import Post, SubscriptionNotification


def mark_as_read(post: Post, user: User):
    """
    Mark the given post as read for the given user.

    :param post: The unread Post instance.
    :param user: The User instance.
    :return: None
    """
    SubscriptionNotification.objects.filter(
        post=post,
        subscription__user=user,
        read__isnull=True,
    ).update(read=timezone.now(), updated=timezone.now())


def check_is_trending(post: Post):
    """
    Determine if the given post is trending.

    :param post: The Post instance.
    :return: bool
    """
    key = f"post.trending.{post.slug}"
    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    views = [timestamp for timestamp in cache.get(key, []) if timestamp >= hour_ago]
    is_trending = len(views) > 5
    views.append(now)
    cache.set(key, views, timeout=600)
    return is_trending
