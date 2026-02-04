from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from django.urls import reverse

from project.newsletter.models import Category, Post


@tag("lab_test")
class TestAdminListViewNPlusOne(TestCase):
    def test_verify_broken(self):
        author = User.objects.create_superuser(username="u1")
        categories = [
            Category.objects.create(slug=f"c{i}", title=f"Cat {i}") for i in range(5)
        ]
        for i in range(5):
            post = Post.objects.create(
                author=author, slug=f"post{i}", title=f"Post {i}"
            )
            post.categories.set(categories)
        client = Client()
        client.force_login(author)

        with self.assertNumQueries(11):
            # This should contain duplicate queries on category
            client.get("/admin/newsletter/post/")


@tag("lab_test")
class TestListViewsCategoriesNPlusOne(TestCase):
    def setUp(self) -> None:
        author = User.objects.create_superuser(username="u1")
        categories = [
            Category.objects.create(slug=f"c{i}", title=f"Cat {i}") for i in range(5)
        ]
        for i in range(5):
            post = Post.objects.create(
                author=author,
                slug=f"post{i}",
                title=f"Post {i}",
                is_public=True,
                is_published=True,
            )
            post.categories.set(categories)
        self.client = Client()
        self.client.force_login(author)

    def test_list_posts(self):
        with self.assertNumQueries(9):
            # This should contain duplicate queries on category
            self.client.get(reverse("newsletter:list_posts"))

    def test_landing(self):
        with self.assertNumQueries(7):
            # This should contain duplicate queries on category
            self.client.get(reverse("newsletter:landing"))


@tag("lab_test")
class TestPostSlugMissingIndex(TestCase):
    def test_sql_uses_scan_without_index(self):
        self.assertIn("scan", Post.objects.filter(slug="test").explain().lower())
        self.assertNotIn("index", Post.objects.filter(slug="test").explain().lower())
