from dataclasses import dataclass

from project.newsletter.models import Category


@dataclass
class CategoryData:
    career: Category
    family: Category
    social: Category
    technical: Category


def generate_data() -> CategoryData:
    social, _ = Category.objects.update_or_create(
        slug="social", defaults={"title": "Social"}
    )
    technical, _ = Category.objects.update_or_create(
        slug="technical", defaults={"title": "Technical"}
    )
    career, _ = Category.objects.update_or_create(
        slug="career", defaults={"title": "Career"}
    )
    family, _ = Category.objects.update_or_create(
        slug="family", defaults={"title": "Family"}
    )
    return CategoryData(
        career=career,
        family=family,
        social=social,
        technical=technical,
    )
