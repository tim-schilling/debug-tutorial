import logging
from contextlib import contextmanager

from django.core.management.base import BaseCommand

from project.data import author, category, markdown, subscribers

logger = logging.getLogger(__name__)


@contextmanager
def log(event):
    logger.info(f"{event} - start")
    yield
    logger.info(f"{event} - end")


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
