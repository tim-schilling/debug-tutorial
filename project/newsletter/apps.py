from django.apps import AppConfig


class NewsletterAppConfig(AppConfig):
    name = "project.newsletter"

    def ready(self):
        from project.newsletter import receivers  # noqa: F401
