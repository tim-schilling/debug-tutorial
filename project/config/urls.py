from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

import project.newsletter.urls

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("account/", include("registration.backends.simple.urls")),
        path("i18n/", include("django.conf.urls.i18n")),
        path("martor/", include("martor.urls")),
        path("", include(project.newsletter.urls)),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

if settings.DEBUG:
    urlpatterns += [  # pragma: no cover
        path("__debug__/", include("debug_toolbar.urls")),
    ]
