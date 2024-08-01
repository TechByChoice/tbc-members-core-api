from celery import shared_task

from .models import UserProfile, EmailTags
from utils.logging_helper import get_logger
from utils.convertkit_service import ConvertKitService

# Create a logger for this module
logger = get_logger(__name__)

@shared_task
def update_convertkit_tags_task(user_profile_id):
    try:
        user_profile = UserProfile.objects.get(id=user_profile_id)
        convertkit_service = ConvertKitService()

        # Fetch all existing tags
        all_tags = set(EmailTags.objects.values_list('name', flat=True))

        # Determine which tags to add and remove based on the user's profile
        add_tags = set(user_profile.skills + [user_profile.role]) & all_tags
        remove_tags = all_tags - add_tags  # Remove tags that are not in the user's current profile

        # Update notification settings tags
        notification_tags = {
            'marketing_monthly_newsletter': 'marketing_monthly_newsletter',
            'marketing_events': 'marketing_events',
            'marketing_jobs': 'marketing_jobs',
            'marketing_org_updates': 'marketing_org_updates',
            'marketing_identity_based_programing': 'marketing_identity_based_programing'


        }
        for field, tag in notification_tags.items():
            if getattr(user_profile, field):
                add_tags.add(tag)
            else:
                remove_tags.add(tag)

        convertkit_service.update_subscriber_tags(user_profile.user.email, add_tags, remove_tags)
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile with id {user_profile_id} does not exist")
    except Exception as e:
        logger.error(f"Error updating ConvertKit tags for UserProfile {user_profile_id}: {str(e)}")
