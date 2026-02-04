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

        with self.assertNumQueries(6):
            # This should contain duplicate queries on category
            response = client.get(reverse("newsletter:analytics"))

        self.assertEqual(
            response.context["aggregates"],
            {
                "Subscriptions": 25,
                "Subscriptions (30 days)": 25,
                "Subscriptions (90 days)": 25,
                "Subscriptions (180 days)": 25,
                "Posts": 5,
                "Posts (30 days)": 5,
                "Posts (90 days)": 5,
                "Posts (180 days)": 5,
            },
        )

        self.assertEqual(
            response.context["subscription_category_aggregates"],
            {f"Cat {i}": 5 for i in range(5)},
        )
        self.assertEqual(
            response.context["post_category_aggregates"],
            {f"Cat {i}": 5 for i in range(5)},
        )
