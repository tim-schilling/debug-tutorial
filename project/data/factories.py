from datetime import UTC, timedelta

import factory
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from faker.utils.text import slugify
from mdgen import MarkdownPostProvider
from mdgen.core import MarkdownImageGenerator

from project.newsletter.models import (
    Category,
    Post,
    Subscription,
    SubscriptionNotification,
)

fake = Faker()
fake.add_provider(MarkdownPostProvider)
Faker.seed(2022)
image_generator = MarkdownImageGenerator()

DATA_END_DATE = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
DATA_START_DATE = DATA_END_DATE - timedelta(days=365 * 2)


def _header(level=1):
    lead = "#" * level
    return lead + fake.sentence()


def _short_photo_update():
    return "\n\n".join(
        [
            _header(level=1),
            fake.paragraph(),
            image_generator.new_image(
                fake.sentence(),
                f"https://picsum.photos/{fake.pyint(200, 500)}",
                fake.text(),
            ),
            fake.paragraph(),
        ]
    )


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.LazyAttribute(
        lambda o: f"{o.first_name}.{o.last_name}.{fake.pyint(max_value=999)}"
    )
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    date_joined = factory.LazyFunction(
        lambda: fake.date_time_between_dates(
            datetime_start=DATA_START_DATE,
            datetime_end=DATA_END_DATE,
            tzinfo=UTC,
        )
    )


class SuperUserFactory(UserFactory):
    is_superuser = True
    is_staff = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    title = factory.Faker("word")
    slug = factory.LazyAttribute(lambda o: slugify(o.title))


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Faker("sentence")
    slug = factory.LazyAttribute(
        lambda o: slugify(o.title) + f"-{fake.pyint(10, 99999)}"
    )
    author = factory.SubFactory(UserFactory)
    content = factory.LazyFunction(lambda: fake.post("medium"))
    summary = factory.Faker("paragraph")
    is_public = True
    is_published = True
    publish_at = factory.LazyFunction(
        lambda: fake.date_time_between_dates(
            datetime_start=DATA_START_DATE,
            datetime_end=DATA_END_DATE,
            tzinfo=UTC,
        )
    )

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)


class ImagePostFactory(PostFactory):
    content = factory.LazyFunction(_short_photo_update)


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)


class SubscriptionNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubscriptionNotification

    subscription = factory.SubFactory(SubscriptionFactory)
    post = factory.SubFactory(PostFactory)
    sent = None
    read = None
