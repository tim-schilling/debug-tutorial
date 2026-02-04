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
from django.db.models import Case, F, Value, When
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from martor.utils import LazyEncoder

from project.newsletter import operations
from project.newsletter.forms import PostForm, SubscriptionForm
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
@require_http_methods(["GET", "POST"])
def create_post(request):
    """
    Staff create post view
    """
    form = PostForm()
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES)
        if form.is_valid():
            form.instance.author = request.user
            post = form.save()
            messages.success(request, f"Post '{post.title}' was created successfully.")
            return redirect("newsletter:update_post", slug=post.slug)
    return render(request, "staff/post_form.html", {"form": form, "post": None})


@staff_member_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET", "POST"])
def update_post(request, slug):
    """
    Staff update post view
    """
    post = get_object_or_404(Post, slug=slug)
    form = PostForm(instance=post)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post, files=request.FILES)
        if form.is_valid():
            form.instance.author = request.user
            post = form.save()
            messages.success(request, f"Post '{post.title}' was updated successfully.")
            return redirect("newsletter:update_post", slug=post.slug)
    return render(request, "staff/post_form.html", {"form": form, "post": post})


def determine_buckets(instance):
    """
    Helper function to determine which buckets should be incremented.

    :param instance: A model instance with ``created`` property.
    :return: tuple(bool, bool, bool)
    """
    now = timezone.now()
    bound_30_days = now - timedelta(days=30)
    bound_90_days = now - timedelta(days=90)
    bound_180_days = now - timedelta(days=180)
    return (
        bound_30_days <= instance.created,
        bound_90_days <= instance.created,
        bound_180_days <= instance.created,
    )


def analyze_categorized_model(Model, label):
    """
    Count the number of instances in the last X days and with a category.

    This can be used with Subscription or Post.
    """
    count = 0
    count_30_days = 0
    count_90_days = 0
    count_180_days = 0
    category_aggregates = {
        category.title: 0 for category in Category.objects.order_by("title")
    }
    for obj in Model.objects.all().prefetch_related("categories"):
        # Increment category buckets
        for category in obj.categories.all():
            category_aggregates[category.title] += 1
        # Increment our post counts
        count += 1
        incr_30, incr_90, incr_180 = determine_buckets(obj)
        if incr_30:
            count_30_days += 1
        if incr_90:
            count_90_days += 1
        if incr_180:
            count_180_days += 1
    return {
        label: count,
        f"{label} (30 days)": count_30_days,
        f"{label} (90 days)": count_90_days,
        f"{label} (180 days)": count_180_days,
    }, category_aggregates


@staff_member_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET"])
def analytics(request):
    """
    The post detail view.
    """
    (
        subscription_aggregates,
        subscription_category_aggregates,
    ) = analyze_categorized_model(Subscription, "Subscriptions")
    post_aggregates, post_category_aggregates = analyze_categorized_model(Post, "Posts")
    return render(
        request,
        "staff/analytics.html",
        {
            "aggregates": {**subscription_aggregates, **post_aggregates},
            "subscription_category_aggregates": subscription_category_aggregates,
            "post_category_aggregates": post_category_aggregates,
        },
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
