from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from martor.models import MartorField


class TimestampedModel(models.Model):
    """Abstract model that adds created and updated timestamps."""

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimestampedModel):
    """Categories of content."""

    title = models.CharField(max_length=512)
    slug = models.SlugField(
        max_length=100,
        allow_unicode=True,
        help_text=_("Unique URL-friendly identifier."),
    )

    class Meta:
        verbose_name_plural = _("categories")
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="category_unq_slug"),
        ]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Category title={self.title} slug={self.slug} created={self.created} updated={self.updated}>"


class Post(TimestampedModel):
    """A piece of content to be drafted and published."""

    title = models.CharField(max_length=512)
    slug = models.SlugField(
        max_length=100,
        allow_unicode=True,
        help_text=_("Unique URL-friendly identifier."),
    )
    author = models.ForeignKey(User, related_name="posts", on_delete=models.PROTECT)
    content = MartorField()
    categories = models.ManyToManyField(Category, blank=True)
    is_published = models.BooleanField(default=False)
    publish_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "If set and Is Published is True, the post will be available after the given value."
        ),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="post_unq_slug"),
        ]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Post title={self.title} slug={self.slug} is_published={self.is_published} created={self.created} updated={self.updated}>"


class Subscription(TimestampedModel):
    """A user's subscriptions to be notified of content of specific categories."""

    user = models.OneToOneField(
        User, related_name="subscription", on_delete=models.CASCADE
    )
    categories = models.ManyToManyField(Category, blank=True)

    def __repr__(self):
        return f"<Subscription id={self.id} user={self.user_id} created={self.created} updated={self.updated}>"


class SubscriptionNotification(TimestampedModel):
    """
    A log of notifications sent per post per subscription.

    When a post is published, any subscribers to the categories of the post
    should be notified of the post.
    """

    subscription = models.ForeignKey(
        Subscription, related_name="notifications", on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post, related_name="subscription_notifications", on_delete=models.CASCADE
    )
    sent = models.DateTimeField(null=True, blank=True)

    def __repr__(self):
        return f"<SubscriptionNotification id={self.id} subscription={self.subscription_id} post={self.post_id} sent={self.sent} created={self.created} updated={self.updated}>"
