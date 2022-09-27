import logging
from contextlib import contextmanager

from django.core.management.base import BaseCommand
from django.utils import timezone

from project.data import (
    author,
    category,
    markdown,
    subscribers,
    subscription_notifications,
)

logger = logging.getLogger(__name__)


@contextmanager
def log(event):
    start = timezone.now()
    logger.info(f"{event} - start")
    yield
    end = timezone.now()
    logger.info(f"{event} - end, {(end-start).total_seconds()}s")


class Command(BaseCommand):
    """Generate fake data for the newsletter app."""

    def handle(self, *args, **options):
        with log("Categories"):
            categories = category.generate_data()

        with log("Posts"):
            markdown.generate_data(
                author.generate_data(),
                categories.social,
                [categories.career, categories.family, categories.technical],
            )
        with log("Subscribers"):
            subscribers.generate_data(categories)

        with log("Subscription Notifications"):
            subscription_notifications.generate_data()
