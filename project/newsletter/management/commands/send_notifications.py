import logging

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from project.newsletter.models import Post, Subscription, SubscriptionNotification

logger = logging.getLogger(__name__)


SUBJECT = _("{name} has made a new post - {title}")
MESSAGE = _("There's a new post. You can view it at: {url}")


class Command(BaseCommand):
    """Send notifications for posts that are published."""

    def iterate_subscription_notifications(self):
        """
        Iterate over subscriptions needing notifications per post.

        Will create a SubscriptionNotification for each Post-Subscription
        pair if it doesn't exist and yield the tuple when the notification
        has not been sent.

        The post will have its notifications_sent property set even if
        there are no subscriptions for the post. This prevents notifications
        from being sent for future subscribers to a given category when the
        post already exists.
        """
        posts = (
            Post.objects.published()
            .needs_notifications_sent()
            .select_related("author")
            .select_for_update(of=("id", "notifications_sent", "updated"))
        )
        with transaction.atomic():
            for post in posts:
                subscriptions = Subscription.objects.needs_notifications_sent(post)
                # Create all notifications so we can safely iterate
                # on sent=False using select_for_update
                SubscriptionNotification.objects.bulk_create(
                    [
                        SubscriptionNotification(subscription=subscription, post=post)
                        for subscription in subscriptions
                    ],
                    ignore_conflicts=True,
                    batch_size=500,
                )
                notifications = (
                    SubscriptionNotification.objects.needs_notifications_sent_for_post(
                        post
                    )
                    .annotate_email()
                    .select_for_update(of=("id", "sent", "updated"))
                )
                for notification in notifications:
                    if notification.email:
                        yield post, notification
                    notification.sent = notification.updated = timezone.now()
                    notification.save(update_fields=["sent", "updated"])
                post.notifications_sent = post.updated = timezone.now()
                post.save(update_fields=["notifications_sent", "updated"])

    def handle(self, *args, **options):
        Post.objects.needs_publishing().update(
            is_published=True, updated=timezone.now()
        )
        for post, notification in self.iterate_subscription_notifications():
            subject = SUBJECT.format(name=post.author.get_full_name(), title=post.title)
            message = MESSAGE.format(
                url=f"https://{get_current_site(None).domain}{post.get_absolute_url()}"
            )
            send_mail(
                subject,
                message,
                from_email=None,
                recipient_list=[notification.email],
            )
