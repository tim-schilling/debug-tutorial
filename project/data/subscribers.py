from collections import OrderedDict
from datetime import UTC, datetime
from functools import partial

from django.contrib.auth.models import User
from faker import Faker

from project.data.category import CategoryData
from project.newsletter.models import Subscription

fake = Faker()
# Seed the randomization to support consistent randomization.
Faker.seed(2022)

USER_COUNT = 100


def generate_data(categories: CategoryData):
    for i in range(0, USER_COUNT, 100):
        users = []
        for _ in range(i, i + 100):
            user = User(first_name=fake.first_name(), last_name=fake.last_name())
            user.username = (
                f"{user.first_name}.{user.last_name}.{fake.pyint(max_value=999)}"
            )
            user.email = f"{user.username}@example.com"
            user.date_joined = fake.date_time_between_dates(
                datetime_start=datetime(2020, 1, 1, tzinfo=UTC),
                datetime_end=datetime(2022, 10, 12, tzinfo=UTC),
                tzinfo=UTC,
            )
            users.append(user)
        User.objects.bulk_create(users, ignore_conflicts=True)
    user_ids = (
        User.objects.exclude(is_staff=True)
        .filter(email__endswith="@example.com")
        .order_by("username")
        .values_list("id", flat=True)
    )
    category_ids = OrderedDict(
        [
            (categories.career.id, 0.3),
            (categories.family.id, 0.9),
            (categories.social.id, 0.5),
            (categories.technical.id, 0.7),
        ]
    )
    get_category_ids = partial(fake.random_elements, elements=category_ids, unique=True)

    for i in range(0, USER_COUNT, 50):
        created_map = {
            user_id: fake.date_time_between_dates(
                datetime_start=datetime(2020, 1, 1, tzinfo=UTC),
                datetime_end=datetime(2022, 10, 12, tzinfo=UTC),
                tzinfo=UTC,
            )
            for user_id in user_ids[i : i + 50]
        }
        Subscription.objects.bulk_create(
            [Subscription(user_id=user_id) for user_id in created_map.keys()],
            ignore_conflicts=True,
        )
        subscriptions = list(Subscription.objects.filter(user__in=user_ids[i : i + 50]))
        for subscription in subscriptions:
            subscription.created = subscription.updated = created_map[
                subscription.user_id
            ]
        Subscription.objects.bulk_update(subscriptions, fields=["created", "updated"])

        through_model = Subscription.categories.through
        through_model.objects.bulk_create(
            [
                through_model(subscription_id=subscription.id, category_id=category_id)
                for subscription in subscriptions
                for category_id in get_category_ids()
            ],
            ignore_conflicts=True,
        )
