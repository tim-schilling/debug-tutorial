from django.urls import path

from project.newsletter.views import markdown_uploader

app_name = "newsletter"
urlpatterns = [
    path("markdown/uploader/", markdown_uploader, name="markdown_uploader"),
]
