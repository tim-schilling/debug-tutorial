from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class ProjectTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically exclude lab_test tagged tests for normal runs.
        # This allows a student to run the test suite after completing the lab
        # without having the lab test error.
        if "lab_test" not in self.tags:
            self.exclude_tags.add("lab_test")

    def setup_databases(self, **kwargs):
        # Force to always delete the database if it exists
        interactive = self.interactive
        self.interactive = False
        try:
            return super().setup_databases(**kwargs)
        finally:
            self.interactive = interactive

    def run_tests(self, *args, **kwargs):

        with override_settings(**TEST_SETTINGS):
            return super().run_tests(*args, **kwargs)


TEST_SETTINGS = {
    "PASSWORD_HASHERS": ["django.contrib.auth.hashers.MD5PasswordHasher"],
}
