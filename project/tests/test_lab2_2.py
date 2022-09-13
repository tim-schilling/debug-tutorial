from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from django.urls import reverse

from project.newsletter.models import Category, Post, Subscription


@tag("lab_test")
class TestAnalytics(TestCase):
    def test_verify_broken(self):
        author = User.objects.create_superuser(username="u1")
        categories = [
            Category.objects.create(slug=f"c{i}", title=f"Cat {i}") for i in range(5)
        ]
        for i in range(5):
            post = Post.objects.create(
                author=author, slug=f"post{i}", title=f"Post {i}"
            )
            post.categories.set(categories)
            subscriber = User.objects.create(username=f"user{i}")
            subscription = Subscription.objects.create(user=subscriber)
            subscription.categories.set(categories)
        client = Client()
        client.force_login(author)

        with self.assertNumQueries(8):
            # This should contain duplicate queries on category
            client.get(reverse("newsletter:analytics"))

    @patch("project.newsletter.views.determine_buckets")
    def test_count_breakdown_calls(self, determine_buckets):
        determine_buckets.return_value = (False, False, False)
        author = User.objects.create_superuser(username="u1")
        categories = [
            Category.objects.create(slug=f"c{i}", title=f"Cat {i}") for i in range(5)
        ]
        for i in range(5):
            post = Post.objects.create(
                author=author, slug=f"post{i}", title=f"Post {i}"
            )
            post.categories.set(categories)
            subscriber = User.objects.create(username=f"user{i}")
            subscription = Subscription.objects.create(user=subscriber)
            subscription.categories.set(categories)
        client = Client()
        client.force_login(author)

        client.get(reverse("newsletter:analytics"))
        self.assertEqual(determine_buckets.call_count, 10)
        determine_buckets.reset_mock()

        # Add more data and verify determine_buckets is called more.
        post = Post.objects.create(author=author, slug="post6", title="Post 6")
        post.categories.set(categories)
        subscriber = User.objects.create(username="user6")
        subscription = Subscription.objects.create(user=subscriber)
        subscription.categories.set(categories)
        client.get(reverse("newsletter:analytics"))
        self.assertEqual(determine_buckets.call_count, 12)
