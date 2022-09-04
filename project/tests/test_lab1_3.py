from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from project.newsletter.models import Post
from project.newsletter.templatetags.newsletter_utils import nice_datetime


@tag("lab_test")
class TestNiceDatetime(TestCase):
    def test_nice_datetime(self):
        post = Post(created=timezone.now())
        actual = nice_datetime(post, is_unread=True)

        self.assertEqual(
            actual, {"timestamp": post.created, "is_recent": True, "is_unread": True}
        )

        post.publish_at = timezone.now() - timedelta(days=7, minutes=1)
        actual = nice_datetime(post, is_unread=False)
        self.assertEqual(
            actual,
            {"timestamp": post.created, "is_recent": True, "is_unread": False},
        )
