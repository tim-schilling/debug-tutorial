from django.contrib.auth.models import User


def generate_data() -> User:
    if user := User.objects.filter(is_superuser=True).order_by("date_joined").first():
        return user

    user, _ = User.objects.get_or_create(
        username="default_user",
        defaults={"first_name": "Django", "last_name": "Pythonista"},
    )
    return user
