from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from project.newsletter.models import Subscription
from project.newsletter.test import DataTestCase


class TestLanding(DataTestCase):
    url = reverse("newsletter:landing")

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "landing.html")
        self.assertEqual(
            list(response.context["posts"]), [self.data.career_post, self.data.all_post]
        )

    def test_authenticated_no_subscription(self):
        self.client.force_login(User.objects.create_user(username="inline"))
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "landing.html")
        self.assertEqual(
            list(response.context["posts"]), [self.data.career_post, self.data.all_post]
        )

    def test_authenticated_subscriber(self):
        self.client.force_login(self.data.subscription.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "landing.html")
        self.assertEqual(
            list(response.context["posts"]),
            [self.data.private_post, self.data.career_post, self.data.all_post],
        )


class TestListPosts(DataTestCase):
    url = reverse("newsletter:list_posts")

    @patch("project.newsletter.views.LIST_POSTS_PAGE_SIZE", 1)
    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "posts/list.html")
        self.assertEqual(list(response.context["page"]), [self.data.career_post])

        self.assertInHTML(
            '<a class="item active" href="?page=1">1</a>',
            response.content.decode("utf-8"),
        )
        self.assertInHTML(
            '<a class="item" href="?page=2">2</a>', response.content.decode("utf-8")
        )

    @patch("project.newsletter.views.LIST_POSTS_PAGE_SIZE", 1)
    def test_authenticated(self):
        self.client.force_login(self.data.subscription.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "posts/list.html")
        self.assertEqual(list(response.context["page"]), [self.data.private_post])

        self.assertInHTML(
            '<a class="item active" href="?page=1">1</a>',
            response.content.decode("utf-8"),
        )
        self.assertInHTML(
            '<a class="item" href="?page=2">2</a>', response.content.decode("utf-8")
        )

    @patch("project.newsletter.views.LIST_POSTS_PAGE_SIZE", 1)
    def test_pagination(self):
        self.client.force_login(self.data.subscription.user)
        response = self.client.get(self.url + "?page=2")
        self.assertTemplateUsed(response, "posts/list.html")
        self.assertEqual(list(response.context["page"]), [self.data.career_post])
        self.assertInHTML(
            '<a class="item" href="?page=1">1</a>', response.content.decode("utf-8")
        )
        self.assertInHTML(
            '<a class="item active" href="?page=2">2</a>',
            response.content.decode("utf-8"),
        )


class TestViewPost(DataTestCase):
    def test_unauthenticated(self):
        response = self.client.get(
            reverse("newsletter:view_post", kwargs={"slug": self.data.career_post.slug})
        )
        self.assertTemplateUsed(response, "posts/detail.html")
        self.assertEqual(response.context["post"], self.data.career_post)

    def test_unauthenticated_private_post(self):
        response = self.client.get(
            reverse(
                "newsletter:view_post", kwargs={"slug": self.data.private_post.slug}
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_authenticated_private_post(self):
        self.client.force_login(self.data.subscription.user)
        response = self.client.get(
            reverse(
                "newsletter:view_post", kwargs={"slug": self.data.private_post.slug}
            )
        )
        self.assertTemplateUsed(response, "posts/detail.html")
        self.assertEqual(response.context["post"], self.data.private_post)


class TestUpdateSubscription(DataTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username="update_subscription")
        self.subscription = Subscription.objects.create(user=self.user)

    def test_unauthenticated(self):
        url = reverse("newsletter:update_subscription")
        response = self.client.get(url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={url}")

    def test_invalid(self):
        self.client.force_login(self.user)
        data = {"categories": True}
        response = self.client.post(
            reverse("newsletter:update_subscription"), data=data
        )
        self.assertTemplateUsed(response, "subscription/update.html")
        self.assertInHTML(
            "<li>Select a valid choice. True is not one of the available choices.</li>",
            response.content.decode("utf-8"),
        )

    def test_update(self):
        self.client.force_login(self.user)
        data = {"categories": [self.data.career.slug]}
        response = self.client.post(
            reverse("newsletter:update_subscription"), data=data
        )
        self.assertRedirects(response, reverse("newsletter:list_posts"))
        self.assertEqual(self.subscription.categories.get(), self.data.career)


class TestAnalytics(DataTestCase):
    def test_basic(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("newsletter:analytics"))
        self.assertTemplateUsed(response, "staff/analytics.html")
        self.assertEqual(
            response.context["aggregates"],
            {
                "Subscribed users": 1,
                "Subscriptions (30 days)": 1,
                "Subscriptions (90 days)": 1,
                "Subscriptions (180 days)": 1,
            },
        )

        self.assertEqual(
            response.context["category_aggregates"],
            {
                self.data.career.title: 1,
                self.data.social.title: 1,
            },
        )

    def test_date_aggregates(self):
        # Create users that are outside the cut-off points.
        # IE: The 180 day user will not appear in the subscription 180 days count
        # because it's beyond the cut-off date.
        for days in [30, 90, 180]:
            user = User.objects.create_user(username=f"days{days}")
            subscription = Subscription.objects.create(user=user)
            # We can't specify created in .create() because it's automatically set.
            Subscription.objects.filter(id=subscription.id).update(
                created=timezone.now() - timedelta(days=days)
            )
            subscription.categories.set([self.data.career, self.data.social])

        self.client.force_login(self.user)
        response = self.client.get(reverse("newsletter:analytics"))
        self.assertTemplateUsed(response, "staff/analytics.html")
        self.assertEqual(
            response.context["aggregates"],
            {
                "Subscribed users": 4,
                "Subscriptions (30 days)": 1,
                "Subscriptions (90 days)": 2,
                "Subscriptions (180 days)": 3,
            },
        )

        self.assertEqual(
            response.context["category_aggregates"],
            {
                self.data.career.title: 4,
                self.data.social.title: 4,
            },
        )
