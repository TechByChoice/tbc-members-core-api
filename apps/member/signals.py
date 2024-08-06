from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.tasks import update_convertkit_tags_task
from .models import MemberProfile


@receiver(post_save, sender=MemberProfile)
def queue_update_convertkit_tags_member_profile(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: update_convertkit_tags_task.delay(instance.user.id))
