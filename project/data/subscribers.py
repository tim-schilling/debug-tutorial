from collections import OrderedDict
from functools import partial

from faker import Faker

from project.data.category import CategoryData
from project.data.factories import SubscriptionFactory, UserFactory
from project.newsletter.models import Subscription

fake = Faker()
Faker.seed(2022)

USER_COUNT = 100


def generate_data(categories: CategoryData):
    users = UserFactory.create_batch(USER_COUNT)

    category_ids = OrderedDict(
        [
            (categories.career.id, 0.3),
            (categories.family.id, 0.9),
            (categories.social.id, 0.5),
            (categories.technical.id, 0.7),
        ]
    )
    category_map = {
        categories.career.id: categories.career,
        categories.family.id: categories.family,
        categories.social.id: categories.social,
        categories.technical.id: categories.technical,
    }
    get_category_ids = partial(fake.random_elements, elements=category_ids, unique=True)

    for user in users:
        if Subscription.objects.filter(user=user).exists():
            continue
        selected_category_ids = get_category_ids()
        selected_categories = [category_map[cid] for cid in selected_category_ids]
        SubscriptionFactory(
            user=user,
            created=user.date_joined,
            updated=user.date_joined,
            categories=selected_categories,
        )
