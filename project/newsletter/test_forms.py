from project.newsletter.forms import SubscriptionForm
from project.newsletter.test import DataTestCase


class TestSubscriptionForm(DataTestCase):
    def test_categories_field_uses_slug_for_value(self):
        form = SubscriptionForm()
        self.assertEqual(
            form.fields["categories"].prepare_value(self.data.social),
            self.data.social.slug,
        )
