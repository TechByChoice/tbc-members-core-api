import logging

import requests
from django.core.management.base import BaseCommand
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


class Command(BaseCommand):
    help = 'Update ConvertKit tags for all users based on their profile information'

    def handle(self, *args, **options):
        convertkit_service = ConvertKitService()
        all_tags = set(EmailTags.objects.filter(
            type__in=MANAGED_TAG_CATEGORIES
        ).values_list('name', flat=True))
        print("Managed tags:", all_tags)

        users = CustomUser.objects.all()
        total_users = users.count()
        processed_users = 0
        print("Total users:", total_users)

        for user in users:
            print("Processing user:", user)
            try:
                with transaction.atomic():
                    print("processing user:", user)
                    self.process_user(user, convertkit_service, all_tags)
                processed_users += 1
                if processed_users % 100 == 0:  # Log progress every 100 users
                    self.stdout.write(f"Processed {processed_users}/{total_users} users")
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {processed_users}/{total_users} users"))

    def process_user(self, user, convertkit_service, all_tags):
        print("Starting Processing user:", user)
        try:
            user_profile = UserProfile.objects.get(user=user)
            member_profile = MemberProfile.objects.get(user=user)
            print("Found user profile:", user_profile)
            print("Found member profile:", member_profile)
        except (UserProfile.DoesNotExist, MemberProfile.DoesNotExist):
            logger.warning(f"User {user.id} is missing UserProfile or MemberProfile")
            return

        add_tags = set()
        remove_tags = set()

        # Skills
        skills = member_profile.skills.values_list('name', flat=True)
        add_tags.update(skill for skill in skills if skill in all_tags)
        print("Added skills tags:", add_tags)

        # Roles
        roles = member_profile.role.values_list('name', flat=True)
        add_tags.update(role for role in roles if role in all_tags)
        print("Added roles tags:", add_tags)

        # Department
        departments = member_profile.department.values_list('name', flat=True)
        add_tags.update(dept for dept in departments if dept in all_tags)
        print("Added departments tags:", add_tags)

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
        print("Added identities tags:", add_tags)

        # Special fields
        if user_profile.disability:
            add_tags.add('Disability')
            print("Added disability tags:", add_tags)
        if user_profile.care_giver:
            add_tags.add('Caregiver')
            print("Added caregiver tags:", add_tags)
        if user_profile.veteran_status:
            add_tags.add('Veteran')
            print("Added veteran tags:", add_tags)

        # Notification settings
        notification_mappings = {
            'marketing_monthly_newsletter': 'marketing_monthly_newsletter',
            'marketing_events': 'marketing_events',
            'marketing_jobs': 'marketing_jobs',
            'marketing_org_updates': 'marketing_org_updates',
            'marketing_identity_based_programing': 'marketing_identity_based_programing'
        }

        for field, tag in notification_mappings.items():
            if tag in all_tags:
                if getattr(user_profile, field):
                    add_tags.add(tag)
                else:
                    remove_tags.add(tag)
        print("Added notifications tags:", add_tags)

        # Remove tags that are in all_tags but not in add_tags
        remove_tags.update(all_tags - add_tags)
        # print("Removed removed tags:", remove_tags)

        # Update tags in ConvertKit
        if add_tags or remove_tags:
            try:
                convertkit_service.update_subscriber_tags(user.email, add_tags, remove_tags)
                logger.info(f"Updated ConvertKit tags for user {user.id}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit reached for user {user.id}. Waiting before retry.")
                    self.handle_rate_limit(e.response)
                    # Retry the update after waiting
                    convertkit_service.update_subscriber_tags(user.email, add_tags, remove_tags)
                else:
                    logger.error(f"Error updating tags for user {user.id}: {str(e)}")
        else:
            logger.info(f"No tag updates needed for user {user.id}")
