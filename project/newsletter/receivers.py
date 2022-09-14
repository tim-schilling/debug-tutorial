from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from project.newsletter.models import Post


@receiver(post_save, sender=Post)
def on_post_save(instance, raw, created, **kwargs):
    if not raw and not created:
        cache.delete(f"post.detail.{instance.slug}")
