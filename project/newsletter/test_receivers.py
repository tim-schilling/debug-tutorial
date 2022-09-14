from django.core.cache import cache
from django.test import Client
from django.urls import reverse

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
        client = Client()
        with self.assertNumQueries(1):
            response = client.get(
                reverse("newsletter:view_post", kwargs={"slug": post.slug})
            )
            self.assertEqual(response.status_code, 200)

        self.assertIsNotNone(cache.get(f"post.detail.{post.slug}"))
        # Trigger the receiver
        post.save()
        self.assertIsNone(cache.get(f"post.detail.{post.slug}"))
        with self.assertNumQueries(1):
            response = client.get(
                reverse("newsletter:view_post", kwargs={"slug": post.slug})
            )
            self.assertEqual(response.status_code, 200)
