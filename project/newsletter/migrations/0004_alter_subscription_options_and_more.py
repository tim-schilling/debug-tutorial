# Generated by Django 4.0.5 on 2022-07-10 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("newsletter", "0003_post_is_public_post_summary"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="subscription",
            options={"ordering": ["-created"]},
        ),
        migrations.AlterModelOptions(
            name="subscriptionnotification",
            options={"ordering": ["-created"]},
        ),
        migrations.AlterField(
            model_name="subscription",
            name="categories",
            field=models.ManyToManyField(
                blank=True, related_name="subscriptions", to="newsletter.category"
            ),
        ),
    ]