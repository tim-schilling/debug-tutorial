from django.core.cache import cache

from project.newsletter.models import Post
from project.newsletter.test import DataTestCase


class TestPostOnSave(DataTestCase):
    def test_clears_cache_on_save(self):
        post = Post.objects.create(
            slug="receiver",
            title="receiver",
            author=self.data.author,
            is_public=True,
            is_published=True,
        )
        cache.set(f"post.detail.{post.slug}", True)
        # Trigger the receiver
        post.save()
        self.assertIsNone(cache.get(f"post.detail.{post.slug}"))
