from datetime import timedelta

from django.core.paginator import Paginator
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from project.newsletter.models import Post
from project.newsletter.templatetags.newsletter_utils import is_ellipsis, nice_datetime


class TestIsEllipsis(SimpleTestCase):
    def test_is_ellipsis(self):
        self.assertTrue(is_ellipsis(Paginator.ELLIPSIS))
        self.assertFalse(is_ellipsis("..."))


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
            {"timestamp": post.publish_at, "is_recent": False, "is_unread": False},
        )
