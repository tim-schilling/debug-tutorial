from django.urls import include, path

from project.newsletter import syndication, views

app_name = "newsletter"
urlpatterns = [
    path("markdown/uploader/", views.markdown_uploader, name="markdown_uploader"),
    path("", views.landing, name="landing"),
    path("account/", views.update_subscription, name="update_subscription"),
    path("analytics/", views.analytics, name="analytics"),
    path("post/unpublished/", views.unpublished_posts, name="unpublished_posts"),
    path("post/create/", views.create_post, name="create_post"),
    path("post/<slug>/update/", views.update_post, name="update_post"),
    path(
        "post/<slug>/toggle_privacy/",
        views.toggle_post_privacy,
        name="toggle_post_privacy",
    ),
    path(
        "p/",
        include(
            [
                path("", views.list_posts, name="list_posts"),
            ]
        ),
    ),
    path(
        "rss/",
        include(
            [
                path("", syndication.RecentPostsFeed()),
                path("<slug>/", syndication.RecentCategorizedPostsFeed()),
            ]
        ),
    ),
]
