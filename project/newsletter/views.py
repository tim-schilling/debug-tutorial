import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Case, Count, F, Q, Value, When
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from martor.utils import LazyEncoder

from project.newsletter import operations
from project.newsletter.forms import SubscriptionForm
from project.newsletter.models import Category, Post, Subscription

LIST_POSTS_PAGE_SIZE = 100


@require_http_methods(["GET"])
def landing(request):
    """
    The landing page view.

    Render the public posts or the most recent posts an authenticated
    user is subscribed for.
    """
    posts = (
        Post.objects.recent_first()
        .published()
        .annotate_is_unread(request.user)
        .prefetch_related("categories")
    )
    if request.user.is_authenticated and (
        subscription := Subscription.objects.for_user(request.user)
    ):
        posts = posts.in_relevant_categories(subscription)
    else:
        posts = posts.public()
    return render(request, "landing.html", {"posts": posts[:3]})


@require_http_methods(["GET"])
def list_posts(request):
    """
    The post lists view.
    """
    posts = (
        Post.objects.recent_first()
        .published()
        .annotate_is_unread(request.user)
        .prefetch_related("categories")
    )
    if not request.user.is_authenticated:
        posts = posts.public()
    paginator = Paginator(posts, LIST_POSTS_PAGE_SIZE)
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
    post = cache.get(f"post.detail.{slug}", None)
    if request.user.is_authenticated or not post:
        posts = Post.objects.published().annotate_is_unread(request.user)
        if not request.user.is_authenticated:
            posts = posts.public()
        post = get_object_or_404(posts, slug=slug)
        if post.is_unread:
            operations.mark_as_read(post, request.user)
        if post.is_public:
            cache.set(f"post.detail.{slug}", post, timeout=600)
    is_trending = operations.check_is_trending(post)
    return render(
        request,
        "posts/detail.html",
        {
            "post": post,
            "is_trending": is_trending,
            "open_graph_url": request.build_absolute_uri(post.get_absolute_url()),
        },
    )


@require_http_methods(["GET", "POST"])
@login_required()
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


@staff_member_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET"])
def unpublished_posts(request):
    """
    The post lists view for unpublished posts
    """
    posts = Post.objects.recent_first().unpublished().prefetch_related("categories")
    paginator = Paginator(posts, LIST_POSTS_PAGE_SIZE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_obj.number)
    return render(
        request, "posts/list.html", {"page": page_obj, "page_range": page_range}
    )


@staff_member_required(login_url=settings.LOGIN_URL)
@require_http_methods(["POST"])
def toggle_post_privacy(request, slug):
    """
    Toggle Post.is_public and redirect back to next url or list view.
    """
    updated = (
        Post.objects.filter(slug=slug)
        .annotate(
            inverted_is_public=Case(
                When(is_public=True, then=Value(False)), default=Value(True)
            )
        )
        .update(is_public=F("inverted_is_public"))
    )
    if not updated:
        raise Http404
    messages.success(request, f"Post slug={slug} was updated.")
    if url := request.GET.get("next"):
        return redirect(url)
    return redirect("newsletter:list_posts")


@staff_member_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET"])
def analytics(request):
    """
    The post detail view.
    """
    now = timezone.now()
    subscription_aggregates = Subscription.objects.all().aggregate(
        subscriptions=Count("user", distinct=True, filter=Q(categories__isnull=False)),
        subscriptions_30_days=Count(
            "id",
            filter=Q(categories__isnull=False, created__gte=now - timedelta(days=30)),
            distinct=True,
        ),
        subscriptions_90_days=Count(
            "id",
            filter=Q(categories__isnull=False, created__gte=now - timedelta(days=90)),
            distinct=True,
        ),
        subscriptions_180_days=Count(
            "id",
            filter=Q(categories__isnull=False, created__gte=now - timedelta(days=180)),
            distinct=True,
        ),
    )
    subscription_category_aggregates = dict(
        Category.objects.annotate(count=Count("subscriptions"))
        .order_by("title")
        .values_list("title", "count")
    )
    post_aggregates = Post.objects.all().aggregate(
        posts=Count("id"),
        posts_30_days=Count(
            "id",
            filter=Q(created__gte=now - timedelta(days=30)),
        ),
        posts_90_days=Count(
            "id",
            filter=Q(created__gte=now - timedelta(days=90)),
        ),
        posts_180_days=Count(
            "id",
            filter=Q(created__gte=now - timedelta(days=180)),
        ),
    )
    post_category_aggregates = dict(
        Category.objects.annotate(count=Count("posts"))
        .order_by("title")
        .values_list("title", "count")
    )

    return render(
        request,
        "staff/analytics.html",
        {
            "aggregates": {
                "Subscriptions": subscription_aggregates["subscriptions"],
                "Subscriptions (30 days)": subscription_aggregates[
                    "subscriptions_30_days"
                ],
                "Subscriptions (90 days)": subscription_aggregates[
                    "subscriptions_90_days"
                ],
                "Subscriptions (180 days)": subscription_aggregates[
                    "subscriptions_180_days"
                ],
                "Posts": post_aggregates["posts"],
                "Posts (30 days)": post_aggregates["posts_30_days"],
                "Posts (90 days)": post_aggregates["posts_90_days"],
                "Posts (180 days)": post_aggregates["posts_180_days"],
            },
            "subscription_category_aggregates": subscription_category_aggregates,
            "post_category_aggregates": post_category_aggregates,
        },
    )


@staff_member_required(login_url=settings.LOGIN_URL)
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
