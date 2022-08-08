import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from martor.utils import LazyEncoder

from project.newsletter.forms import SubscriptionForm
from project.newsletter.models import Post, Subscription


@require_http_methods(["GET"])
def landing(request):
    """
    The landing page view.

    Render the public posts or the most recent posts an authenticated
    user is subscribed for.
    """
    posts = Post.objects.recent_first().published().public()
    if request.user.is_authenticated and (
        subscription := Subscription.objects.for_user(request.user)
    ):
        posts = posts.in_relevant_categories(subscription)
    return render(request, "landing.html", {"posts": posts[:3]})


@require_http_methods(["GET"])
def list_posts(request):
    """
    The post lists view.
    """
    posts = Post.objects.recent_first().published()
    if not request.user.is_authenticated:
        posts = posts.public()
    paginator = Paginator(posts, 100)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)
    return render(
        request, "posts/list.html", {"page": page_obj, "page_range": page_range}
    )


@require_http_methods(["GET"])
def view_post(request, slug):
    """
    The post detail view.
    """
    posts = Post.objects.published()
    if not request.user.is_authenticated:
        posts = posts.public()
    post = get_object_or_404(posts, slug=slug)
    return render(request, "posts/detail.html", {"post": post})


@require_http_methods(["GET", "POST"])
@login_required
def update_subscription(request):
    instance = Subscription.objects.filter(user=request.user).first()
    form = SubscriptionForm(instance=instance)
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=instance)
        if form.is_valid():
            if not instance:
                form.instance.user = request.user
            form.save()
            messages.success(request, "Your subscription changes have been saved.")
            return redirect("newsletter:list_posts")
    return render(request, "subscription/update.html", {"form": form})


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
