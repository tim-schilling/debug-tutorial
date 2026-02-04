from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase, tag

from project.newsletter.models import Post
from project.newsletter.views import view_post


@tag("lab_test")
class TestViewPost(TestCase):
    def test_verify_broken(self):
        post = Post.objects.create(
            author=User.objects.create(username="u1"), slug="post", title="Post"
        )
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        self.assertRaises(Post.DoesNotExist, view_post, request, post.slug)
