from typing import Optional

from django.contrib.auth.models import AnonymousUser, User
from django.core import validators
from django.db import models
from django.db.models import Exists, F, OuterRef
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from martor.models import MartorField


class TimestampedModel(models.Model):
    """Abstract model that adds created and updated timestamps."""

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created"]


class Category(TimestampedModel):
    """Categories of content."""

    title = models.CharField(max_length=512)
    slug = models.CharField(
        max_length=100,
        validators=[validators.validate_unicode_slug],
        help_text=_("Unique URL-friendly identifier."),
    )

    class Meta:
        verbose_name_plural = _("categories")
        ordering = ["title"]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Category title={self.title} slug={self.slug} created={self.created} updated={self.updated}>"


class PostQuerySet(models.QuerySet):
    def recent_first(self):
        """Order by so most recently published or created are first."""
        return self.order_by(Coalesce("publish_at", "created").desc())

    def public(self):
        """Limit to those that are published."""
        return self.filter(is_public=True)

    def published(self):
        """Limit to those that are published."""
        return self.filter(is_published=True)

    def unpublished(self):
        """Limit to those that are unpublished."""
        return self.filter(is_published=False)

    def needs_publishing(self, now=None):
        """Limit to those that aren't published, but are scheduled to be."""
        now = now or timezone.now()
        return self.filter(is_published=False, publish_at__lte=now)

    def needs_notifications_sent(self):
        """Limit to those that have yet to send out notifications to their subscribers."""
        return self.filter(notifications_sent__isnull=True)

    def in_category(self, category: Category):
        """Limit to the given category"""
        return self.filter(categories=category)

    def in_relevant_categories(self, subscription):
        """
        Limit to the categories for the subscription

        :param subscription: The Subscription instance.
        :return: a Post QuerySet.
        """
        return self.filter(categories__subscriptions=subscription).distinct()

    def annotate_is_unread(self, user):
        """
        Annotate is_unread onto the Post queryset.

        If the user is authenticated, determine if the user was sent a
        notification regarding the post, but hasn't read it.

        If the user is unauthenticated (AnonymousUser), then mark all
        posts as "read".

        :param user: The User instance.
        :return: a Post QuerySet.
        """
        if isinstance(user, AnonymousUser):
            return self.annotate(is_unread=models.Value(False))
        return self.annotate(
            is_unread=Exists(
                SubscriptionNotification.objects.filter(
                    post_id=OuterRef("id"),
                    subscription__user=user,
                    sent__isnull=False,
                    read__isnull=True,
                )
            )
        )


class Post(TimestampedModel):
    """A piece of content to be drafted and published."""

    title = models.CharField(max_length=512)
    slug = models.CharField(
        max_length=100,
        validators=[validators.validate_unicode_slug],
        help_text=_("Unique URL-friendly identifier."),
    )
    author = models.ForeignKey(User, related_name="posts", on_delete=models.PROTECT)
    content = MartorField()
    summary = MartorField()
    categories = models.ManyToManyField(Category, related_name="posts", blank=True)
    is_public = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    publish_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "If set and Is Published is True, the post will be available after the given value."
        ),
    )
    notifications_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "If set, all notifications are considered to have been sent and will not be sent again."
        ),
    )
    open_graph_description = models.TextField(
        blank=True, help_text=_("Used for SEO purposes and social media sharing.")
    )
    open_graph_image = models.ImageField(
        null=True,
        blank=True,
        upload_to="open_graph/",
        help_text=_("Used for SEO purposes and social media sharing."),
    )
    objects = models.Manager.from_queryset(PostQuerySet)()

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Post title={self.title} slug={self.slug} is_published={self.is_published} created={self.created} updated={self.updated}>"

    @property
    def publish_date(self):
        return self.publish_at or self.created

    def get_absolute_url(self):
        return reverse("newsletter:view_post", kwargs={"slug": self.slug})


class SubscriptionQuerySet(models.QuerySet):
    def for_user(self, user: User) -> Optional["Subscription"]:
        """
        Fetch the subscription for the user if it exists.
        :param user: The User instance.
        :return: The subscription instance if it exists.
        """
        return self.filter(user=user).first()

    def needs_notifications_sent(self, post: Post):
        """
        Limit to those that need to send notifications for the post.

        :param post: The Post instance.
        :return: a Subscription QuerySet.
        """
        return self.filter(
            models.Q(notifications__post=post, notifications__sent__isnull=True)
            | models.Q(notifications__post__isnull=True),
            categories__posts=post,
            user__date_joined__lte=post.publish_date,
        )


class Subscription(TimestampedModel):
    """A user's subscriptions to be notified of content of specific categories."""

    user = models.OneToOneField(
        User, related_name="subscription", on_delete=models.CASCADE
    )
    categories = models.ManyToManyField(
        Category,
        related_name="subscriptions",
        blank=True,
        help_text=_(
            "An email will be sent when post matching one of these categories is published."
        ),
    )
    objects = models.Manager.from_queryset(SubscriptionQuerySet)()

    def __repr__(self):
        return f"<Subscription id={self.id} user={self.user_id} created={self.created} updated={self.updated}>"


class SubscriptionNotificationQuerySet(models.QuerySet):
    def needs_notifications_sent_for_post(self, post: Post):
        """
        Limit to those that need to send notifications for the post.

        :param post: The Post instance.
        :return: a SubscriptionNotification QuerySet.
        """
        return self.filter(post=post, sent__isnull=True)

    def annotate_email(self):
        """
        Annotate the SubscriptionNotification QuerySet with the subscriber's email.

        :return: a SubscriptionNotification QuerySet.
        """
        return self.annotate(email=F("subscription__user__email"))


class SubscriptionNotification(TimestampedModel):
    """
    A log of notifications sent per post per subscription.

    When a post is published, any subscribers to the categories of the post
    should be notified of the post.
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "subscription"], name="subscript_notif_uniq"
            )
        ]

    subscription = models.ForeignKey(
        Subscription, related_name="notifications", on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post, related_name="subscription_notifications", on_delete=models.CASCADE
    )
    sent = models.DateTimeField(null=True, blank=True)
    read = models.DateTimeField(null=True, blank=True)
    objects = models.Manager.from_queryset(SubscriptionNotificationQuerySet)()

    def __repr__(self):
        return f"<SubscriptionNotification id={self.id} subscription={self.subscription_id} post={self.post_id} sent={self.sent} created={self.created} updated={self.updated}>"
