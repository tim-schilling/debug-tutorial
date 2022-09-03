from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.utils import timezone

from project.newsletter.models import Post, Subscription, SubscriptionNotification
from project.newsletter.test import DataTestCase


class TestCategory(DataTestCase):
    def test_str(self):
        self.assertEqual(str(self.data.career), self.data.career.title)


class TestPost(DataTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.post = Post.objects.create(
            author=self.data.author,
            slug="test-post",
            title="Test Post",
            content="content",
        )
        self.post.categories.set([self.data.career, self.data.social])

    def test_str(self):
        self.assertEqual(str(self.data.all_post), self.data.all_post.title)

    def test_publish_date(self):
        self.assertEqual(self.post.publish_date, self.post.created)
        self.post.publish_at = timezone.now()
        self.assertEqual(self.post.publish_date, self.post.publish_at)

    def test_get_absolute_url(self):
        self.assertEqual(self.data.all_post.get_absolute_url(), "/p/all-post/")

    def test_recent_first(self):
        # Create a new post that's a copy of all_post
        self.assertEqual(Post.objects.recent_first().first(), self.post)
        # Set publish_at to a value that's older than private_post's created
        self.post.publish_at = timezone.now() - timedelta(days=10)
        self.post.save()
        self.assertEqual(Post.objects.recent_first().first(), self.data.private_post)

    def test_public(self):
        self.assertTrue(Post.objects.public().filter(id=self.data.all_post.id).exists())
        self.assertFalse(
            Post.objects.public().filter(id=self.data.private_post.id).exists()
        )

    def test_published(self):
        self.post.is_published = False
        self.post.save()
        self.assertTrue(
            Post.objects.published().filter(id=self.data.all_post.id).exists()
        )
        self.assertFalse(Post.objects.published().filter(id=self.post.id).exists())

    def test_unpublished(self):
        self.post.is_published = False
        self.post.save()
        self.assertFalse(
            Post.objects.unpublished().filter(id=self.data.all_post.id).exists()
        )
        self.assertTrue(Post.objects.unpublished().filter(id=self.post.id).exists())

    def test_needs_publishing(self):
        self.post.is_published = False
        self.post.publish_at = timezone.now() + timedelta(days=1)
        self.post.save()
        self.assertFalse(
            Post.objects.needs_publishing().filter(id=self.post.id).exists()
        )
        # Verify the `or param` path
        self.assertTrue(
            Post.objects.needs_publishing(timezone.now() + timedelta(days=1, minutes=1))
            .filter(id=self.post.id)
            .exists()
        )
        # Exclude it via publish_at
        self.post.is_published = True
        self.post.save()
        self.assertFalse(
            Post.objects.needs_publishing().filter(id=self.post.id).exists()
        )

    def test_needs_notifications_sent(self):
        self.assertTrue(
            Post.objects.needs_notifications_sent().filter(id=self.post.id).exists()
        )
        self.post.notifications_sent = timezone.now()
        self.post.save()
        self.assertFalse(
            Post.objects.needs_notifications_sent().filter(id=self.post.id).exists()
        )

    def test_in_category(self):
        self.assertTrue(
            Post.objects.in_category(self.data.social)
            .filter(id=self.data.all_post.id)
            .exists()
        )
        self.assertTrue(
            Post.objects.in_category(self.data.career)
            .filter(id=self.data.all_post.id)
            .exists()
        )
        self.assertTrue(
            Post.objects.in_category(self.data.social)
            .filter(id=self.data.private_post.id)
            .exists()
        )
        self.assertFalse(
            Post.objects.in_category(self.data.career)
            .filter(id=self.data.private_post.id)
            .exists()
        )

    def test_in_relevant_categories(self):
        self.assertTrue(
            Post.objects.in_relevant_categories(self.data.subscription)
            .filter(id=self.data.all_post.id)
            .exists()
        )
        self.assertTrue(
            Post.objects.in_relevant_categories(self.data.subscription)
            .filter(id=self.data.private_post.id)
            .exists()
        )

        user = User.objects.create_user(username="in_relevant_categories")
        subscription = Subscription.objects.create(user=user)
        subscription.categories.set([self.data.social])
        self.assertTrue(
            Post.objects.in_relevant_categories(subscription)
            .filter(id=self.data.all_post.id)
            .exists()
        )
        self.assertFalse(
            Post.objects.in_relevant_categories(subscription)
            .filter(id=self.data.career_post.id)
            .exists()
        )
        self.assertTrue(
            Post.objects.in_relevant_categories(subscription)
            .filter(id=self.data.private_post.id)
            .exists()
        )

    def test_annotate_is_unread(self):
        notification = SubscriptionNotification.objects.create(
            subscription=self.data.subscription,
            post=self.data.all_post,
        )
        # Test unsent
        self.assertFalse(
            Post.objects.annotate_is_unread(self.data.subscription.user)
            .get(id=self.data.all_post.id)
            .is_unread
        )
        notification.sent = timezone.now()
        notification.save()
        # Test valid case
        self.assertTrue(
            Post.objects.annotate_is_unread(self.data.subscription.user)
            .get(id=self.data.all_post.id)
            .is_unread
        )
        # Test unauthenticated user case
        self.assertFalse(
            Post.objects.annotate_is_unread(AnonymousUser())
            .get(id=self.data.all_post.id)
            .is_unread
        )
        notification.read = timezone.now()
        notification.save()
        # Test read notification case
        self.assertFalse(
            Post.objects.annotate_is_unread(self.data.subscription.user)
            .get(id=self.data.all_post.id)
            .is_unread
        )


class TestSubscription(DataTestCase):
    def test_for_user(self):
        self.assertEqual(
            Subscription.objects.for_user(self.data.subscription.user),
            self.data.subscription,
        )
        self.assertEqual(Subscription.objects.for_user(self.data.author), None)

    def test_needs_notifications_sent(self):
        user = User.objects.create_user(username="needs_notifications_sent")
        subscription = Subscription.objects.create(user=user)
        subscription.categories.set([self.data.social])
        # The post must be created after the user.
        post = Post.objects.create(
            author=self.data.author,
            title="Needs notifications",
            slug="needs-notifications",
            content="content",
        )
        post.categories.set([self.data.social])
        self.assertTrue(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )

        notification = subscription.notifications.create(post=post, sent=timezone.now())
        self.assertFalse(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )
        notification.sent = None
        notification.save()
        self.assertTrue(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )

        subscription.categories.set([self.data.career])
        self.assertFalse(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )
        subscription.categories.set([self.data.social])
        self.assertTrue(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )
        user.date_joined = timezone.now()
        user.save()
        self.assertFalse(
            Subscription.objects.needs_notifications_sent(post)
            .filter(id=subscription.id)
            .exists()
        )
