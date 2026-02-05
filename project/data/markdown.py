from datetime import timedelta
from itertools import cycle

from project.data.factories import DATA_END_DATE, ImagePostFactory, PostFactory
from project.newsletter.models import Post

POST_COUNT = 1500

RECENT_POSTS = [
    {"title": "Welcome to Our Newsletter", "slug": "welcome-to-our-newsletter"},
    {"title": "Getting Started with Python", "slug": "getting-started-with-python"},
    {"title": "Advanced Django Techniques", "slug": "advanced-django-techniques"},
    {"title": "Database Optimization Tips", "slug": "database-optimization-tips"},
    {"title": "Testing Best Practices", "slug": "testing-best-practices"},
    {"title": "Debugging Like a Pro", "slug": "debugging-like-a-pro"},
    {"title": "Code Review Guidelines", "slug": "code-review-guidelines"},
    {"title": "Deployment Strategies", "slug": "deployment-strategies"},
    {"title": "Security Fundamentals", "slug": "security-fundamentals"},
    {"title": "Performance Monitoring", "slug": "performance-monitoring"},
]


def generate_data(user, image_category, post_categories):
    image_posts = ImagePostFactory.build_batch(
        POST_COUNT,
        author=user,
    )
    Post.objects.bulk_create(image_posts, batch_size=500, ignore_conflicts=True)

    category_through = Post.categories.through
    category_through.objects.bulk_create(
        [
            category_through(category_id=image_category.id, post_id=post_id)
            for post_id in Post.objects.filter(categories__isnull=True).values_list(
                "id", flat=True
            )
        ],
        batch_size=500,
        ignore_conflicts=True,
    )

    general_posts = PostFactory.build_batch(
        POST_COUNT,
        author=user,
    )
    Post.objects.bulk_create(general_posts, batch_size=500, ignore_conflicts=True)

    category_cycle = cycle(post_categories)
    category_through.objects.bulk_create(
        [
            category_through(category_id=next(category_cycle).id, post_id=post_id)
            for post_id in Post.objects.filter(categories__isnull=True).values_list(
                "id", flat=True
            )
        ],
        batch_size=500,
        ignore_conflicts=True,
    )

    recent_posts = [
        PostFactory.build(
            author=user,
            title=post_data["title"],
            slug=post_data["slug"],
            publish_at=DATA_END_DATE - timedelta(days=i),
            created=DATA_END_DATE - timedelta(days=i),
        )
        for i, post_data in enumerate(RECENT_POSTS)
    ]
    Post.objects.bulk_create(recent_posts, ignore_conflicts=True)

    category_cycle = cycle(post_categories)
    category_through.objects.bulk_create(
        [
            category_through(category_id=next(category_cycle).id, post_id=post.id)
            for post in recent_posts
        ],
        ignore_conflicts=True,
    )
