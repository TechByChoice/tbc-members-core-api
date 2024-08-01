from django.db import transaction
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from apps.core.tasks import update_convertkit_tags_task
from .models import CustomUser, UserProfile
from ..member.models import MemberProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        MemberProfile.objects.create(user=instance)


@receiver(post_save, sender=UserProfile)
def queue_update_convertkit_tags(sender, instance, created, **kwargs):
    # Queue the task to update ConvertKit tags
    transaction.on_commit(lambda: update_convertkit_tags_task.delay(instance.user.id))
