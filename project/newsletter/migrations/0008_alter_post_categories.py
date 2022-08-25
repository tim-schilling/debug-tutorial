# Generated by Django 4.0.5 on 2022-08-20 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("newsletter", "0007_alter_subscriptionnotification_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="categories",
            field=models.ManyToManyField(
                blank=True, related_name="posts", to="newsletter.category"
            ),
        ),
    ]