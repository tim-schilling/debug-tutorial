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
