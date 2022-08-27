from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from project.newsletter.management.commands.send_notifications import Command
from project.newsletter.models import Category, Post, Subscription


class TestSendNotifications(TestCase):
    def setUp(self) -> None:
        self.command = Command()

    def iterate_subscription_notifications(self):
        category = Category.objects.create(title="Cat", slug="cat")
        author = User.objects.create(username="author")
        subscription1 = Subscription.objects.create(
            user=User.objects.create(username="subscriber1")
        )
        subscription2 = Subscription.objects.create(
            user=User.objects.create(username="subscriber2")
        )
        subscription1.categories.set([category])
        subscription2.categories.set([category])

        post = Post.objects.create(
            author=author,
            title="title",
            slug="slug",
            is_published=True,
            content="content",
        )
        post.categories.set([category])
        notification1 = subscription1.notifications.create(post=post)
        subscription2.notifications.create(post=post, sent=timezone.now())

        self.assertEqual(
            list(self.command.iterate_subscription_notifications()),
            [(post, notification1)],
        )
        post.refresh_from_db()
        self.assertIsNotNone(post.notifications_sent)

    @patch("project.newsletter.management.commands.send_notifications.send_mail")
    def test_email(self, send_mail):
        category = Category.objects.create(title="Cat", slug="cat")
        author = User.objects.create(
            username="author", first_name="Alex", last_name="Star"
        )
        subscription = Subscription.objects.create(
            user=User.objects.create(username="subscriber", email="alex@example.com")
        )
        subscription.categories.set([category])

        post = Post.objects.create(
            author=author,
            title="title",
            slug="slug",
            is_published=True,
            content="content",
        )
        post.categories.set([category])

        call_command("send_notifications")

        self.assertIsNotNone(subscription.notifications.get().sent)
        send_mail.assert_called_once_with(
            "Alex Star has made a new post - title",
            "There's a new post. You can view it at: https://example.com/p/slug/",
            from_email=None,
            recipient_list=["alex@example.com"],
        )
