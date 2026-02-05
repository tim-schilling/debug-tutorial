from dataclasses import dataclass

from project.data.factories import CategoryFactory
from project.newsletter.models import Category


@dataclass
class CategoryData:
    career: Category
    family: Category
    social: Category
    technical: Category


def generate_data() -> CategoryData:
    social = CategoryFactory(slug="social", title="Social")
    technical = CategoryFactory(slug="technical", title="Technical")
    career = CategoryFactory(slug="career", title="Career")
    family = CategoryFactory(slug="family", title="Family")
    return CategoryData(
        career=career,
        family=family,
        social=social,
        technical=technical,
    )
