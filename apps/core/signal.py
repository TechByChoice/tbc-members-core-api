from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=UserProfile)
def update_convertkit_tags(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: update_convertkit_tags_task.delay(instance.id))
    else:
        # Check if relevant fields have changed
        if instance.tracker.has_changed('skills') or instance.tracker.has_changed(
                'role') or instance.tracker.has_changed('notification_settings'):
            transaction.on_commit(lambda: update_convertkit_tags_task.delay(instance.id))


from .tasks import update_convertkit_tags_task
