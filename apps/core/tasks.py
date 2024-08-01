import logging

from celery import shared_task
from django.db import transaction

from apps.core.models import CustomUser, UserProfile, EmailTags
from apps.member.models import MemberProfile
from utils.convertkit_service import ConvertKitService

logger = logging.getLogger(__name__)

MANAGED_TAG_CATEGORIES = [
    'identity',
    'notification',
    'skill',
    'department',
    'role'
]


@shared_task
def update_convertkit_tags_task(user_id):
    print(f'update_convertkit_tags_task for {user_id}')
    try:
        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)
            convertkit_service = ConvertKitService()
            all_tags = set(EmailTags.objects.filter(
                type__in=MANAGED_TAG_CATEGORIES
            ).values_list('name', flat=True))

            process_user(user, convertkit_service, all_tags)
    except CustomUser.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
    except Exception as e:
        logger.error(f"Error updating ConvertKit tags for user {user_id}: {str(e)}")


def process_user(user, convertkit_service, all_tags):
    try:
        user_profile = UserProfile.objects.get(user=user)
        member_profile = MemberProfile.objects.get(user=user)
    except (UserProfile.DoesNotExist, MemberProfile.DoesNotExist):
        logger.warning(f"User {user.id} is missing UserProfile or MemberProfile")
        return

    add_tags = set()
    remove_tags = set()

    # Skills
    skills = member_profile.skills.values_list('name', flat=True)
    add_tags.update(skill for skill in skills if skill in all_tags)

    # Roles
    roles = member_profile.role.values_list('name', flat=True)
    add_tags.update(role for role in roles if role in all_tags)

    # Department
    departments = member_profile.department.values_list('name', flat=True)
    add_tags.update(dept for dept in departments if dept in all_tags)

    # Identity info
    identity_fields = [
        'identity_sexuality',
        'identity_gender',
        'identity_ethic',
        'identity_pronouns',
    ]

    for field in identity_fields:
        identities = getattr(user_profile, field).values_list('name', flat=True)
        add_tags.update(identity for identity in identities if identity in all_tags)

    # Special fields
    if user_profile.disability:
        add_tags.add('Disability')
    if user_profile.care_giver:
        add_tags.add('Caregiver')
    if user_profile.veteran_status:
        add_tags.add('Veteran')

    # Notification settings
    notification_fields = [
        'marketing_monthly_newsletter',
        'marketing_events',
        'marketing_jobs',
        'marketing_org_updates',
        'marketing_identity_based_programing',
    ]

    for field in notification_fields:
        if getattr(user_profile, field):
            add_tags.add(field)
        else:
            remove_tags.add(field)

    # Remove tags that are in all_tags but not in add_tags
    remove_tags.update(all_tags - add_tags)

    # Update tags in ConvertKit
    if add_tags or remove_tags:
        try:
            convertkit_service.update_subscriber_tags(user.email, add_tags, remove_tags)
            logger.info(f"Updated ConvertKit tags for user {user.id}")
        except Exception as e:
            logger.error(f"Error updating tags for user {user.id}: {str(e)}")
    else:
        logger.info(f"No tag updates needed for user {user.id}")
