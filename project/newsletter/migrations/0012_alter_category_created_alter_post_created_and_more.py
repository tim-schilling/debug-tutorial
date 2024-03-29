# Generated by Django 4.1.1 on 2022-09-26 03:16

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "newsletter",
            "0011_alter_post_options_remove_category_category_unq_slug_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="created",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="created",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="created",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False
            ),
        ),
        migrations.AlterField(
            model_name="subscriptionnotification",
            name="created",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False
            ),
        ),
    ]
