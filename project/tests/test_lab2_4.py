from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, tag
from django.urls import reverse

from project.newsletter.models import Post


@tag("lab_test")
class TestPostDetailCaching(TestCase):
    def test_verify_broken(self):
        author = User.objects.create_superuser(username="u1")
        post = Post.objects.create(
            author=author,
            slug="lab2.4",
            title="Post lab2.4",
            is_public=True,
            is_published=True,
        )
        client = Client()
        response = client.get(
            reverse("newsletter:view_post", kwargs={"slug": post.slug})
        )
        self.assertEqual(response.status_code, 200)

        Post.objects.filter(id=post.id).update(is_public=False)
        response = client.get(
            reverse("newsletter:view_post", kwargs={"slug": post.slug})
        )
        self.assertEqual(response.status_code, 200)

        cache.delete(f"post.detail.{post.slug}")
        response = client.get(
            reverse("newsletter:view_post", kwargs={"slug": post.slug})
        )
        self.assertEqual(response.status_code, 404)
