# Generated by Django 4.0.5 on 2022-08-16 01:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("newsletter", "0005_auto_20220809_0012"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ["title"], "verbose_name_plural": "categories"},
        ),
        migrations.AlterField(
            model_name="subscription",
            name="categories",
            field=models.ManyToManyField(
                blank=True,
                help_text="An email will be sent when post matching one of these categories is published.",
                related_name="subscriptions",
                to="newsletter.category",
            ),
        ),
    ]
