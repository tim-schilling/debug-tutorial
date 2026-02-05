from django.db.models import F

from project.data.factories import SubscriptionNotificationFactory
from project.newsletter.models import Post, Subscription, SubscriptionNotification


def generate_data():
    posts = list(Post.objects.published().recent_first()[:100])
    date = max(p.publish_date for p in posts)

    subscriber_ids = (
        Subscription.objects.filter(
            categories__posts__in=posts,
            user__date_joined__lte=date,
        )
        .values_list("id", flat=True)
        .distinct()
    )

    notifications = []
    for subscription_id in subscriber_ids:
        for post in posts:
            if not SubscriptionNotification.objects.filter(
                post=post, subscription_id=subscription_id
            ).exists():
                notifications.append(
                    SubscriptionNotificationFactory.build(
                        post=post,
                        subscription_id=subscription_id,
                        sent=date,
                    )
                )

    SubscriptionNotification.objects.bulk_create(notifications, batch_size=10000)
    SubscriptionNotification.objects.filter(post__in=posts).update(
        created=F("sent"),
        updated=F("sent"),
    )
    Post.objects.filter(id__in=[post.id for post in posts]).update(
        notifications_sent=date
    )
