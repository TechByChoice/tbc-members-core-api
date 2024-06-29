from django.shortcuts import get_object_or_404

from apps.mentorship.models import MentorProfile, MenteeProfile, MentorshipProgramProfile, CommitmentLevel
from .logging_helper import get_logger, log_exception, timed_function

logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def update_support_type(user, data):
    """
    Update the support type for a mentorship program profile.

    This function updates the commitment level and support areas for mentors and mentees.

    Args:
        user (User): The user for whom to update the support type.
        data (dict): The data containing commitment level and support area IDs.

    Returns:
        None
    """
    logger.info(f"Updating support type for user: {user.username}")

    program_profile = get_object_or_404(MentorshipProgramProfile, user=user)
    commitment_data = data.get("commitment_level_id")
    if commitment_data:
        program_profile.commitment_level.set(CommitmentLevel.objects.filter(id__in=commitment_data))
        program_profile.save()
        logger.info(f"Updated commitment level for user: {user.username}")

    if user.is_mentor:
        mentor_profile = get_object_or_404(MentorProfile, user=user)
        support_area_ids = data.get("mentor_support_areas_id", [])
        if commitment_data:
            mentor_profile.mentor_commitment_level.set(CommitmentLevel.objects.filter(id__in=commitment_data))
        if support_area_ids:
            program_profile.mentor_support_areas.set(support_area_ids)
        mentor_profile.save()
        logger.info(f"Updated mentor support areas for user: {user.username}")

    if user.is_mentee:
        mentee_profile = get_object_or_404(MenteeProfile, user=user)
        mentee_support_area_ids = data.get("mentee_support_areas_id", [])
        if mentee_support_area_ids:
            mentee_profile.mentee_support_areas.set(mentee_support_area_ids)
        mentee_profile.save()
        logger.info(f"Updated mentee support areas for user: {user.username}")


@log_exception(logger)
@timed_function(logger)
def submit_application(user, data):
    """
    Submit an application for a mentorship program.

    This function updates or creates the mentor and mentee profiles and links them to the mentorship program profile.

    Args:
        user (User): The user submitting the application.
        data (dict): The data containing support areas for mentor and mentee profiles.

    Returns:
        None
    """
    logger.info(f"Submitting mentorship application for user: {user.username}")

    mentor_profile, created = MentorProfile.objects.update_or_create(
        user=user, defaults={"mentor_support_areas": data.get("mentor_support_areas")}
    )
    logger.info(f"Mentor profile {'created' if created else 'updated'} for user: {user.username}")

    mentee_profile, created = MenteeProfile.objects.update_or_create(
        user=user, defaults={"mentee_support_areas": data.get("mentee_support_areas")}
    )
    logger.info(f"Mentee profile {'created' if created else 'updated'} for user: {user.username}")

    program_profile = get_object_or_404(MentorshipProgramProfile, user=user)
    program_profile.mentor_profile = mentor_profile
    program_profile.mentee_profile = mentee_profile
    program_profile.save()
    logger.info(f"Mentorship program profile updated for user: {user.username}")
