from django.core.paginator import Paginator
from django.test import SimpleTestCase

from project.newsletter.templatetags.newsletter_utils import is_ellipsis


class TestIsEllipsis(SimpleTestCase):
    def test_is_ellipsis(self):
        self.assertTrue(is_ellipsis(Paginator.ELLIPSIS))
        self.assertFalse(is_ellipsis("..."))
