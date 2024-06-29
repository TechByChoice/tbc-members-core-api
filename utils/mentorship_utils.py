import logging
from functools import wraps
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from apps.core.models import CustomUser
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data
from apps.mentorship.models import MentorProfile, MenteeProfile, MentorshipProgramProfile, MentorRoster, Session
from apps.mentorship.serializer import MentorRosterSerializer, MentorReviewSerializer

logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def create_mentorship_relationship(mentor_id, mentee_user):
    """
    Create a mentorship relationship between a mentor and a mentee.

    This function handles the creation of a MentorRoster instance and associated Session.
    It also ensures that the mentee has a MenteeProfile and updates the user's mentee status.

    Args:
        mentor_id (int): The ID of the mentor's MentorProfile.
        mentee_user (CustomUser): The user object of the mentee.

    Returns:
        dict: A dictionary containing the status of the operation and any relevant data.

    Raises:
        ObjectDoesNotExist: If the mentor profile is not found.
        Exception: For any other unexpected errors during the process.
    """
    logger.info(f"Attempting to create mentorship relationship: Mentor ID {mentor_id}, Mentee User ID {mentee_user.id}")

    try:
        with transaction.atomic():
            mentor = MentorProfile.objects.get(id=mentor_id)

            mentee_profile, created = MenteeProfile.objects.get_or_create(user=mentee_user)
            if created:
                logger.info(f"Created new MenteeProfile for user {mentee_user.id}")
                mentee_user.is_mentee = True
                mentee_user.save()

            roster_data = {"mentor": mentor.id, "mentee": mentee_profile.id}
            serializer = MentorRosterSerializer(data=roster_data)

            if serializer.is_valid():
                mentor_roster = serializer.save()
                Session.objects.create(mentor_mentee_connection=mentor_roster, created_by=mentee_user)
                logger.info(f"Created mentorship relationship: Roster ID {mentor_roster.id}")
                return {"status": True, "message": "Mentorship relationship created successfully",
                        "data": serializer.data}
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return {"status": False, "message": "Failed to create mentorship relationship",
                        "errors": serializer.errors}

    except ObjectDoesNotExist:
        logger.error(f"Mentor profile not found for ID {mentor_id}")
        return {"status": False, "message": "Mentor profile not found"}
    except Exception as e:
        logger.exception(f"Unexpected error in create_mentorship_relationship: {str(e)}")
        return {"status": False, "message": "An unexpected error occurred"}


@log_exception(logger)
@timed_function(logger)
def submit_mentor_review(mentor_id, mentee_user, rating, review_content):
    """
    Submit a review for a mentor by a mentee.

    This function creates a MentorReview instance with the provided data.

    Args:
        mentor_id (int): The ID of the mentor's MentorProfile.
        mentee_user (CustomUser): The user object of the mentee submitting the review.
        rating (int): The rating given by the mentee (typically on a scale, e.g., 1-5).
        review_content (str): The text content of the review.

    Returns:
        dict: A dictionary containing the status of the operation and any relevant data.

    Raises:
        ObjectDoesNotExist: If the mentor or mentee profile is not found.
        Exception: For any other unexpected errors during the process.
    """
    logger.info(f"Attempting to submit mentor review: Mentor ID {mentor_id}, Mentee User ID {mentee_user.id}")

    try:
        mentor = MentorProfile.objects.get(id=mentor_id)
        mentee = MenteeProfile.objects.get(user=mentee_user)

        review_data = {
            "mentor": mentor.id,
            "mentee": mentee.id,
            "rating": rating,
            "review_content": review_content,
            "review_author": "mentee",
        }

        serializer = MentorReviewSerializer(data=review_data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Mentor review submitted successfully: Mentor ID {mentor_id}, Mentee ID {mentee.id}")
            return {"status": True, "message": "Mentor review submitted successfully", "data": serializer.data}
        else:
            logger.error(f"Serializer validation failed: {serializer.errors}")
            return {"status": False, "message": "Failed to submit mentor review", "errors": serializer.errors}

    except ObjectDoesNotExist as e:
        logger.error(f"Profile not found: {str(e)}")
        return {"status": False, "message": "Mentor or mentee profile not found"}
    except Exception as e:
        logger.exception(f"Unexpected error in submit_mentor_review: {str(e)}")
        return {"status": False, "message": "An unexpected error occurred"}


@log_exception(logger)
@timed_function(logger)
def update_mentor_application_status(mentor_id, new_status, updated_by_user, additional_data=None):
    """
    Update the application status of a mentor.

    This function handles various status updates for a mentor's application, including
    rejection, pausing, approval, and activation. It also manages associated tasks like
    sending emails and creating necessary accounts.

    Args:
        mentor_id (int): The ID of the mentor's CustomUser instance.
        new_status (str): The new status to set for the mentor's application.
        updated_by_user (CustomUser): The user making the status update.
        additional_data (dict, optional): Any additional data required for the status update.

    Returns:
        dict: A dictionary containing the status of the operation and any relevant messages.

    Raises:
        ObjectDoesNotExist: If the mentor profiles are not found.
        Exception: For any other unexpected errors during the process.
    """
    logger.info(f"Attempting to update mentor application status: Mentor ID {mentor_id}, New Status {new_status}")

    try:
        with transaction.atomic():
            mentor_user = CustomUser.objects.get(id=mentor_id)
            program_profile = MentorshipProgramProfile.objects.get(user=mentor_user)
            mentor_profile = MentorProfile.objects.get(user=mentor_user)

            if new_status == "rejected":
                return _handle_mentor_rejection(mentor_user, mentor_profile, program_profile, additional_data)
            elif new_status == "paused":
                return _handle_mentor_paused(mentor_user, mentor_profile)
            elif new_status == "approved":
                return _handle_mentor_approval(mentor_user, mentor_profile, program_profile)
            elif new_status == "active":
                return _handle_mentor_activation(mentor_user, mentor_profile, program_profile)
            else:
                logger.warning(f"Invalid status update requested: {new_status}")
                return {"status": False, "message": "Invalid status update"}

    except ObjectDoesNotExist as e:
        logger.error(f"Profile not found: {str(e)}")
        return {"status": False, "message": "Mentor profile not found"}
    except Exception as e:
        logger.exception(f"Unexpected error in update_mentor_application_status: {str(e)}")
        return {"status": False, "message": "An unexpected error occurred"}


# Helper functions for update_mentor_application_status

def _handle_mentor_rejection(mentor_user, mentor_profile, program_profile, additional_data):
    mentor_user.is_mentor_profile_active = False
    mentor_user.is_mentor_profile_removed = True
    mentor_user.is_mentor = False
    mentor_profile.removed_date = datetime.utcnow()
    mentor_profile.mentor_status = additional_data.get("rejection_reason", "rejected")

    mentor_user.save()
    mentor_profile.save()
    program_profile.save()

    # TODO: Implement email sending logic for rejection
    logger.info(f"Mentor application rejected: Mentor ID {mentor_user.id}")
    return {"status": True, "message": "Mentor application rejected successfully"}


def _handle_mentor_paused(mentor_user, mentor_profile):
    mentor_user.is_mentor_active = False
    mentor_profile.mentor_status = "paused"
    mentor_profile.paused_date = datetime.utcnow()

    mentor_user.save()
    mentor_profile.save()

    # TODO: Implement email sending logic for paused status
    logger.info(f"Mentor application paused: Mentor ID {mentor_user.id}")
    return {"status": True, "message": "Mentor application paused successfully"}


def _handle_mentor_approval(mentor_user, mentor_profile, program_profile):
    mentor_user.is_mentor_interviewing = False
    mentor_user.is_mentor_profile_approved = True
    mentor_profile.mentor_status = "need_cal_info"

    # TODO: Implement logic for creating TBC email and sending approval email
    logger.info(f"Mentor application approved: Mentor ID {mentor_user.id}")
    return {"status": True, "message": "Mentor application approved successfully"}


def _handle_mentor_activation(mentor_user, mentor_profile, program_profile):
    mentor_user.is_mentor_profile_active = True
    mentor_user.is_mentor_profile_paused = False
    mentor_user.is_mentor_profile_removed = False
    mentor_profile.activated_at_date = datetime.utcnow()
    mentor_profile.mentor_status = "active"

    mentor_user.save()
    mentor_profile.save()
    program_profile.save()

    # TODO: Implement email sending logic for activation
    logger.info(f"Mentor activated: Mentor ID {mentor_user.id}")
    return {"status": True, "message": "Mentor activated successfully"}
