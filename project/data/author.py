from django.contrib.auth.models import User

from project.data.factories import SuperUserFactory


def generate_data() -> User:
    if user := User.objects.filter(is_superuser=True).order_by("date_joined").first():
        return user

    return SuperUserFactory(
        username="default_user",
        first_name="Django",
        last_name="Pythonista",
    )
