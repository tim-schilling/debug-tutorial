from dataclasses import dataclass

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from project.newsletter.models import Category, Post, Subscription


@dataclass
class TestData:
    author: User
    career: Category
    social: Category
    all_post: Post
    career_post: Post
    private_post: Post
    subscription: Subscription


def create_test_data() -> TestData:
    author = User.objects.create_user(
        username="author",
        email="author@example.com",
        first_name="Author",
        last_name="Name",
    )
    career = Category.objects.create(title="Career", slug="career")
    social = Category.objects.create(title="Social", slug="social")
    all_post = Post.objects.create(
        title="All category post",
        slug="all-post",
        author=author,
        content="# Title",
        summary="## Summary",
        is_published=True,
        is_public=True,
        notifications_sent=timezone.now(),
    )
    all_post.categories.set([career, social])
    career_post = Post.objects.create(
        title="Career post",
        slug="career-post",
        author=author,
        content="# Title",
        summary="## Summary",
        is_published=True,
        is_public=True,
        notifications_sent=timezone.now(),
    )
    career_post.categories.set([career])
    private_post = Post.objects.create(
        title="Private post",
        slug="private-post",
        author=author,
        content="# Title",
        summary="## Summary",
        is_published=True,
        is_public=False,
        notifications_sent=timezone.now(),
    )
    private_post.categories.set([social])

    subscriber = User.objects.create_user(
        username="subscriber",
        email="subscriber@example.com",
        first_name="Subscriber",
        last_name="Name",
    )
    subscription = Subscription.objects.create(user=subscriber)
    subscription.categories.set([career, social])

    return TestData(
        author=author,
        career=career,
        social=social,
        all_post=all_post,
        career_post=career_post,
        private_post=private_post,
        subscription=subscription,
    )


class DataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.data = create_test_data()

    def setUp(self) -> None:
        self.rf = RequestFactory()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test",
            first_name="Admin",
            last_name="User",
        )
