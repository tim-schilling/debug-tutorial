# Generated by Django 4.0.5 on 2022-08-09 00:12

from django.db import migrations


def create_site(apps, schema_editor):  # pragma: nocover
    Site = apps.get_model("sites", "Site")
    site = Site.objects.filter(domain="example.com").first()
    if site:
        site.name = "Debug Newsletter"
        site.domain = "127.0.0.1:8000"
        site.save()


class Migration(migrations.Migration):

    dependencies = [
        ("newsletter", "0004_alter_subscription_options_and_more"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(create_site, migrations.RunPython.noop),
    ]
