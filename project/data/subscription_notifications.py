from django.db.models import F

from project.newsletter.models import Post, Subscription, SubscriptionNotification


def generate_data():
    post_qs = Post.objects.published()
    post_count = post_qs.count()
    batch = 50
    for i in range(0, post_count, batch):
        posts = post_qs[i : i + batch]
        date = max(p.publish_date for p in posts)

        subscriber_ids = (
            Subscription.objects.filter(
                categories__posts__id__in=posts,
                user__date_joined__lte=date,
            )
            .values_list("id", flat=True)
            .distinct()
        )

        SubscriptionNotification.objects.bulk_create(
            [
                SubscriptionNotification(post=post, subscription_id=id, sent=date)
                for id in subscriber_ids
                for post in posts
            ],
            batch_size=10000,
        )
        SubscriptionNotification.objects.filter(post__in=posts).update(
            created=F("sent"),
            updated=F("sent"),
        )
        Post.objects.filter(id__in=[post.id for post in posts]).update(
            notifications_sent=date
        )
