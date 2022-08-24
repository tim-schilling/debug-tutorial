import logging

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from project.newsletter.models import Post, Subscription, SubscriptionNotification

logger = logging.getLogger(__name__)


SUBJECT = _("{name} has made a new post - {title}")
MESSAGE = _("There's a new post. You can view it at: {url}")


class Command(BaseCommand):
    """Send notifications for posts that are published."""

    def iterate_subscription_notifications(self):
        posts = (
            Post.objects.published().needs_notifications_sent().select_related("author")
        )
        for post in posts:
            subscriptions = Subscription.objects.needs_notifications_sent(post)
            for subscription in subscriptions:
                notification, _ = SubscriptionNotification.objects.get_or_create(
                    subscription=subscription,
                    post=post,
                )
                if notification.sent:
                    continue
                yield post, notification
            post.notifications_sent = post.updated = timezone.now()
            post.save(update_fields=["notifications_sent", "updated"])

    def handle(self, *args, **options):
        Post.objects.needs_publishing().update(
            is_published=True, updated=timezone.now()
        )

        for post, notification in self.iterate_subscription_notifications():
            with transaction.atomic():
                # Reselect the notification in a transaction block to prevent
                # multiple processes from sending a notification at once.
                notification = (
                    SubscriptionNotification.objects.annotate(
                        email=F("subscription__user__email")
                    )
                    .select_for_update(of=("id", "sent", "updated"))
                    .get(id=notification.id)
                )

                subject = SUBJECT.format(
                    name=post.author.get_full_name(), title=post.title
                )
                message = MESSAGE.format(
                    url=f"https://{get_current_site(None).domain}{post.get_absolute_url()}"
                )
                send_mail(
                    subject,
                    message,
                    from_email=None,
                    recipient_list=[notification.email],
                )
                notification.sent = notification.updated = timezone.now()
                notification.save(update_fields=["sent", "updated"])
