import os
import uuid

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from martor.utils import LazyEncoder


@staff_member_required
@require_http_methods(["POST"])
def markdown_uploader(request):
    """
    Markdown image upload for locale storage
    and represent as json to markdown editor.

    Taken from https://github.com/agusmakmun/django-markdown-editor/wiki
    """
    if "markdown-image-upload" in request.FILES:
        image = request.FILES["markdown-image-upload"]
        image_types = [
            "image/png",
            "image/jpg",
            "image/jpeg",
            "image/pjpeg",
            "image/gif",
        ]
        if image.content_type not in image_types:
            return JsonResponse(
                {"status": 405, "error": _("Bad image format.")},
                encoder=LazyEncoder,
                status=405,
            )

        if image.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            to_MB = settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024 * 1024)
            return JsonResponse(
                {
                    "status": 405,
                    "error": _("Maximum image file is %(size)s MB.") % {"size": to_MB},
                },
                encoder=LazyEncoder,
                status=405,
            )

        img_uuid = "{}-{}".format(uuid.uuid4().hex[:10], image.name.replace(" ", "-"))
        tmp_file = os.path.join(settings.MARTOR_UPLOAD_PATH, img_uuid)
        def_path = default_storage.save(tmp_file, ContentFile(image.read()))
        img_url = os.path.join(settings.MEDIA_URL, def_path)

        return JsonResponse({"status": 200, "link": img_url, "name": image.name})
    return HttpResponse(_("Invalid request!"))
