from datetime import datetime, timezone, time, timedelta

from faker import Faker

TODAY = datetime.combine(datetime.now().date(), time.min, tzinfo=timezone.utc)

fake = Faker()
# Seed the randomization to support consistent randomization.
Faker.seed(2022)


def fake_date():
    return TODAY - timedelta(days=fake.random_int(0, 500))
