from django.contrib import admin
from martor.tests.models import Post

from project.newsletter.admin import (
    PostAdmin,
    SubscriptionAdmin,
    SubscriptionNotificationAdmin,
)
from project.newsletter.models import Subscription, SubscriptionNotification
from project.newsletter.test import DataTestCase


class TestPostAdmin(DataTestCase):
    def test_categories_list(self):
        model_admin = PostAdmin(Post, admin.site)
        self.assertEqual(
            model_admin.categories_list(self.data.all_post), "Career, Social"
        )
        self.assertEqual(model_admin.categories_list(self.data.career_post), "Career")

    def test_get_changeform_initial_data(self):
        model_admin = PostAdmin(Post, admin.site)
        request = self.rf.get("/")
        request.user = self.user
        self.assertEqual(
            model_admin.get_changeform_initial_data(request),
            {"author": self.user},
        )


class TestSubscriptionAdmin(DataTestCase):
    def test_categories_list(self):
        model_admin = SubscriptionAdmin(Subscription, admin.site)
        self.assertEqual(
            model_admin.categories_list(self.data.subscription), "Career, Social"
        )

    def test_user_email(self):
        model_admin = SubscriptionAdmin(Subscription, admin.site)
        self.assertEqual(
            model_admin.user_email(self.data.subscription),
            "subscriber@example.com",
        )


class TestSubscriptionNotificationAdmin(DataTestCase):
    def test_user_email(self):
        notification = SubscriptionNotification.objects.create(
            post=self.data.all_post,
            subscription=self.data.subscription,
        )
        model_admin = SubscriptionNotificationAdmin(
            SubscriptionNotification, admin.site
        )
        self.assertEqual(
            model_admin.user_email(notification),
            "subscriber@example.com",
        )
