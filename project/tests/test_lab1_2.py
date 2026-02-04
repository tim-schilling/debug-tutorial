from io import BytesIO

from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from django.urls import reverse
from PIL import Image

from project.newsletter.models import Post


@tag("lab_test")
class TestUpdatePost(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="lab1_2")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_get_broken(self):
        response = self.client.get(reverse("newsletter:create_post"))
        self.assertNotContains(response, ' enctype="multipart/form-data"')

    def test_create_post_broken(self):
        img = BytesIO()
        Image.new("RGB", (1, 1), "#FF0000").save(img, format="PNG")
        img.name = "myimage.png"
        img.seek(0)
        data = {
            "title": "Test Create",
            "slug": "test-create",
            "categories": [],
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
        self.assertIsNone(post.open_graph_image._file)

    def test_update_get_broken(self):
        post = Post.objects.create(
            author=self.user,
            title="Test Update",
            slug="test-update",
            content="c",
        )
        response = self.client.get(
            reverse("newsletter:update_post", kwargs={"slug": post.slug})
        )
        self.assertNotContains(response, ' enctype="multipart/form-data"')

    def test_update_post_broken(self):
        post = Post.objects.create(
            author=self.user,
            title="Test Update",
            slug="test-update",
            content="c",
        )
        img = BytesIO()
        Image.new("RGB", (1, 1), "#FF0000").save(img, format="PNG")
        img.name = "myimage.png"
        img.seek(0)
        data = {
            "title": "Test Update",
            "slug": "test-update",
            "categories": [],
            "content": "content",
            "summary": "summary",
            "is_public": False,
            "is_published": True,
            "open_graph_description": "description",
            "open_graph_image": img,
        }
        url = reverse("newsletter:update_post", kwargs={"slug": post.slug})
        response = self.client.post(url, data=data)

        self.assertRedirects(response, url)
        post.refresh_from_db()
        self.assertIsNone(post.open_graph_image._file)
