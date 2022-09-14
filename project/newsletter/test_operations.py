from django.core.cache import cache

from project.newsletter import operations
from project.newsletter.models import SubscriptionNotification
from project.newsletter.test import DataTestCase


class TestMarkAsRead(DataTestCase):
    def test_mark_as_read(self):
        notification = SubscriptionNotification.objects.create(
            subscription=self.data.subscription,
            post=self.data.all_post,
        )
        operations.mark_as_read(self.data.all_post, self.data.subscription.user)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read)


class TestCheckIsTrending(DataTestCase):
    def test_check_is_trending(self):
        cache.delete(f"post.trending.{self.data.all_post.slug}")
        for i in range(6):
            self.assertFalse(operations.check_is_trending(self.data.all_post))
        self.assertTrue(operations.check_is_trending(self.data.all_post))
        cache.delete(f"post.trending.{self.data.all_post.slug}")
