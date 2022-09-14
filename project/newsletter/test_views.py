from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from project.newsletter.models import Post, Subscription, SubscriptionNotification
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
        # Verify the categories are rendered
        self.assertContains(response, self.data.career_post.categories.first().title)

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

        # Verify the pagination exists.
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

        # Verify the categories are rendered
        self.assertContains(response, self.data.private_post.categories.first().title)
        # Verify the pagination exists.
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
        # Verify the pagination exists.
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

    def test_mark_as_read(self):
        notification = SubscriptionNotification.objects.create(
            subscription=self.data.subscription,
            post=self.data.all_post,
            sent=timezone.now(),
        )
        self.client.force_login(self.data.subscription.user)
        response = self.client.get(
            reverse("newsletter:view_post", kwargs={"slug": self.data.all_post.slug})
        )
        self.assertTemplateUsed(response, "posts/detail.html")
        self.assertEqual(response.context["post"], self.data.all_post)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read)

    def test_cached_response(self):
        post = Post.objects.create(
            slug="cached",
            title="cached",
            author=self.data.author,
            is_public=True,
            is_published=True,
        )
        with self.assertNumQueries(1):
            self.client.get(reverse("newsletter:view_post", kwargs={"slug": post.slug}))

        with self.assertNumQueries(0):
            self.client.get(reverse("newsletter:view_post", kwargs={"slug": post.slug}))


class TestUnpublishedPosts(DataTestCase):
    url = reverse("newsletter:unpublished_posts")

    def setUp(self):
        super().setUp()
        self.unpublished_post1 = Post.objects.create(
            author=self.data.author,
            title="Unpublished 1",
            slug="unpublished-1",
            is_published=False,
            is_public=False,
        )
        self.unpublished_post2 = Post.objects.create(
            author=self.data.author,
            title="Unpublished 2",
            slug="unpublished-2",
            is_published=False,
            is_public=True,
        )

    def test_staff_user_required(self):
        user = User.objects.create_user(username="basic")
        self.client.force_login(user)
        response = self.client.post(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    @patch("project.newsletter.views.LIST_POSTS_PAGE_SIZE", 1)
    def test_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "posts/list.html")
        self.assertEqual(list(response.context["page"]), [self.unpublished_post2])

        self.assertInHTML(
            '<a class="item active" href="?page=1">1</a>',
            response.content.decode("utf-8"),
        )
        self.assertInHTML(
            '<a class="item" href="?page=2">2</a>', response.content.decode("utf-8")
        )

    @patch("project.newsletter.views.LIST_POSTS_PAGE_SIZE", 1)
    def test_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + "?page=2")
        self.assertTemplateUsed(response, "posts/list.html")
        self.assertEqual(list(response.context["page"]), [self.unpublished_post1])
        self.assertInHTML(
            '<a class="item" href="?page=1">1</a>', response.content.decode("utf-8")
        )
        self.assertInHTML(
            '<a class="item active" href="?page=2">2</a>',
            response.content.decode("utf-8"),
        )


class TestUpdatePost(DataTestCase):
    def test_staff_user_required(self):
        user = User.objects.create_user(username="basic")
        self.client.force_login(user)
        url = reverse(
            "newsletter:update_post", kwargs={"slug": self.data.private_post.slug}
        )
        response = self.client.post(url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={url}")

    def test_get(self):
        self.client.force_login(self.user)
        url = reverse(
            "newsletter:update_post", kwargs={"slug": self.data.private_post.slug}
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "staff/post_form.html")

    def test_invalid(self):
        self.client.force_login(self.user)
        url = reverse(
            "newsletter:update_post", kwargs={"slug": self.data.private_post.slug}
        )
        response = self.client.post(url, data={})
        self.assertTemplateUsed(response, "staff/post_form.html")
        self.assertInHTML(
            "<li>This field is required.</li>",
            response.content.decode("utf-8"),
        )

    def test_update(self):
        post = Post.objects.create(
            author=self.data.author,
            title="Test Update",
            slug="test-update",
            content="c",
        )
        self.client.force_login(self.user)

        img = BytesIO()
        Image.new("RGB", (1, 1), "#FF0000").save(img, format="PNG")
        img.name = "myimage.png"
        img.seek(0)
        data = {
            "title": "Test Update2",
            "slug": "test-update2",
            "categories": [self.data.career.id],
            "content": "content",
            "summary": "summary",
            "is_public": False,
            "is_published": True,
            "open_graph_description": "description",
            "open_graph_image": img,
        }
        response = self.client.post(
            reverse("newsletter:update_post", kwargs={"slug": post.slug}), data=data
        )
        self.assertRedirects(
            response, reverse("newsletter:update_post", kwargs={"slug": "test-update2"})
        )
        post.refresh_from_db()
        self.assertEqual(post.slug, "test-update2")
        self.assertEqual(post.title, "Test Update2")
        self.assertEqual(post.categories.get(), self.data.career)
        self.assertEqual(post.content, "content")
        self.assertEqual(post.summary, "summary")
        self.assertEqual(post.open_graph_description, "description")
        self.assertFalse(post.is_public)
        self.assertTrue(post.is_published)
        self.assertIsNotNone(post.open_graph_image.file)


class TestTogglePostPrivacy(DataTestCase):
    def test_staff_user_required(self):
        user = User.objects.create_user(username="basic")
        self.client.force_login(user)
        url = reverse(
            "newsletter:toggle_post_privacy",
            kwargs={"slug": self.data.private_post.slug},
        )
        response = self.client.post(url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={url}")

    def test_toggle_404(self):
        self.client.force_login(self.user)
        url = reverse("newsletter:toggle_post_privacy", kwargs={"slug": "invalid"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_toggle(self):
        self.client.force_login(self.user)

        post = Post.objects.create(
            author=self.data.author,
            title="Test toggle",
            slug="test-toggle",
            content="c",
            is_public=True,
        )
        url = reverse("newsletter:toggle_post_privacy", kwargs={"slug": post.slug})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("newsletter:list_posts"))
        post.refresh_from_db()
        self.assertFalse(post.is_public)

        # Toggle the property back and verify the redirect to next.
        response = self.client.post(
            url
            + f'?next={reverse("newsletter:update_post", kwargs={"slug": post.slug})}'
        )
        self.assertRedirects(
            response, reverse("newsletter:update_post", kwargs={"slug": post.slug})
        )
        post.refresh_from_db()
        self.assertTrue(post.is_public)


class TestCreatePost(DataTestCase):
    def test_staff_user_required(self):
        user = User.objects.create_user(username="basic")
        self.client.force_login(user)
        url = reverse("newsletter:create_post")
        response = self.client.post(url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={url}")

    def test_get(self):
        self.client.force_login(self.user)
        url = reverse("newsletter:create_post")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "staff/post_form.html")

    def test_invalid(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("newsletter:create_post"), data={})
        self.assertTemplateUsed(response, "staff/post_form.html")
        self.assertInHTML(
            "<li>This field is required.</li>",
            response.content.decode("utf-8"),
        )

    def test_create(self):
        self.client.force_login(self.user)

        img = BytesIO()
        Image.new("RGB", (1, 1), "#FF0000").save(img, format="PNG")
        img.name = "myimage.png"
        img.seek(0)
        data = {
            "title": "Test Create",
            "slug": "test-create",
            "categories": [self.data.career.id],
            "content": "content",
            "summary": "summary",
            "is_public": False,
            "is_published": True,
            "open_graph_description": "description",
            "open_graph_image": img,
        }
        response = self.client.post(reverse("newsletter:create_post"), data=data)

        self.assertRedirects(
            response, reverse("newsletter:update_post", kwargs={"slug": "test-create"})
        )
        post = Post.objects.get(slug="test-create")
        self.assertEqual(post.title, "Test Create")
        self.assertEqual(post.categories.get(), self.data.career)
        self.assertEqual(post.content, "content")
        self.assertEqual(post.summary, "summary")
        self.assertEqual(post.open_graph_description, "description")
        self.assertFalse(post.is_public)
        self.assertTrue(post.is_published)
        self.assertIsNotNone(post.open_graph_image.file)


class TestUpdateSubscription(DataTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username="update_subscription")
        self.subscription = Subscription.objects.create(user=self.user)

    def test_unauthenticated(self):
        url = reverse("newsletter:update_subscription")
        response = self.client.get(url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={url}")

    def test_get(self):
        self.client.force_login(self.user)
        url = reverse("newsletter:update_subscription")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "subscription/update.html")

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
                "Subscriptions": 1,
                "Subscriptions (30 days)": 1,
                "Subscriptions (90 days)": 1,
                "Subscriptions (180 days)": 1,
                "Posts": 3,
                "Posts (30 days)": 3,
                "Posts (90 days)": 3,
                "Posts (180 days)": 3,
            },
        )

        self.assertEqual(
            response.context["subscription_category_aggregates"],
            {
                self.data.career.title: 1,
                self.data.social.title: 1,
            },
        )
        self.assertEqual(
            response.context["post_category_aggregates"],
            {
                self.data.career.title: 2,
                self.data.social.title: 2,
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
                "Subscriptions": 4,
                "Subscriptions (30 days)": 1,
                "Subscriptions (90 days)": 2,
                "Subscriptions (180 days)": 3,
                "Posts": 3,
                "Posts (30 days)": 3,
                "Posts (90 days)": 3,
                "Posts (180 days)": 3,
            },
        )

        self.assertEqual(
            response.context["subscription_category_aggregates"],
            {
                self.data.career.title: 4,
                self.data.social.title: 4,
            },
        )
        self.assertEqual(
            response.context["post_category_aggregates"],
            {
                self.data.career.title: 2,
                self.data.social.title: 2,
            },
        )
