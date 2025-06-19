from datetime import timezone
from itertools import cycle

from faker import Faker
from faker.utils.text import slugify
from mdgen import MarkdownPostProvider
from mdgen.core import MarkdownImageGenerator

from project.newsletter.models import Post
from project.data import dates

fake = Faker()
fake.add_provider(MarkdownPostProvider)
# Seed the randomization to support consistent randomization.
Faker.seed(2022)
image_generator = MarkdownImageGenerator()


def header(level=1):
    lead = "#" * level
    return lead + fake.sentence()


def short_photo_update():
    return "\n\n".join(
        [
            header(level=1),
            fake.paragraph(),
            image_generator.new_image(
                fake.sentence(),
                f"https://picsum.photos/{fake.pyint(200, 500)}",
                fake.text(),
            ),
            fake.paragraph(),
        ]
    )


def generate_data(user, image_category, post_categories):
    image_posts = []
    for i in range(1500):
        title = fake.sentence()
        slug = slugify(title) + f"-{fake.pyint(10, 99999)}"
        publish_at = (
            dates.fake_date()
            if fake.pybool()
            else None
        )
        created = dates.fake_date()
        if publish_at and publish_at < created:
            created = publish_at
        image_posts.append(
            Post(
                created=created,
                author=user,
                title=title,
                slug=slug,
                summary=fake.paragraph(),
                content=short_photo_update(),
                is_public=True,
                is_published=True,
                publish_at=publish_at,
            )
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

    general_posts = []
    for i in range(1500):
        title = fake.sentence()
        slug = slugify(title) + f"-{fake.pyint(10, 9999)}"
        publish_at = (
            dates.fake_date()
            if fake.pybool()
            else None
        )
        created = dates.fake_date()
        if publish_at and publish_at < created:
            created = publish_at
        general_posts.append(
            Post(
                created=created,
                author=user,
                title=title,
                slug=slug,
                summary=fake.paragraph(),
                content=fake.post("medium"),
                is_public=True,
                is_published=True,
                publish_at=publish_at,
            )
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

    last_post = Post.objects.published().recent_first().first()
    last_post.slug = 'extraordinary-things-happen-all-over-123456'
    last_post.title = "120 year old points out extraordinary things happen everywhere"
    last_post.save()