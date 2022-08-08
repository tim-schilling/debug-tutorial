from django.core.management.base import BaseCommand

from project.data import category, markdown, user


class Command(BaseCommand):
    """Generate fake data for the newsletter app."""

    def handle(self, *args, **options):
        categories = category.generate_data()
        author = user.generate_data()
        markdown.generate_data(
            author,
            categories.social,
            [categories.career, categories.family, categories.technical],
        )
