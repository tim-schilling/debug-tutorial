"""
This file contains create/update/writing operations.
"""
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
