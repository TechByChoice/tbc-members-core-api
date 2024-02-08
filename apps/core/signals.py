from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile
from ..talent.models import TalentProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        TalentProfile.objects.create(user=instance)
