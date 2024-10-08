import logging
from functools import wraps
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from apps.company.models import CompanyProfile
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def get_user_profile(user_id):
    """
    Retrieve a user's profile by their user ID.

    This function attempts to fetch a user's profile from the database. It includes
    error handling for cases where the profile doesn't exist and logs the operation.

    Args:
        user_id (int): The unique identifier of the user.

    Returns:
        UserProfile: The user's profile if found.

    Raises:
        ObjectDoesNotExist: If no profile is found for the given user_id.
    """
    from apps.core.models import UserProfile

    logger.info(f"Attempting to retrieve profile for user_id: {user_id}")
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        logger.info(f"Successfully retrieved profile for user_id: {user_id}")
        return profile
    except ObjectDoesNotExist:
        logger.error(f"No profile found for user_id: {user_id}")
        raise


@log_exception(logger)
@timed_function(logger)
def update_user_profile(user_id, profile_data):
    """
    Update a user's profile with the provided data.

    This function updates an existing user profile with new data. It uses a database
    transaction to ensure data integrity and logs the operation.

    Args:
        user_id (int): The unique identifier of the user whose profile is being updated.
        profile_data (dict): A dictionary containing the fields to be updated and their new values.

    Returns:
        UserProfile: The updated user profile.

    Raises:
        ObjectDoesNotExist: If no profile is found for the given user_id.
    """
    from apps.core.models import UserProfile

    logger.info(f"Attempting to update profile for user_id: {user_id}")
    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user_id=user_id)
            sanitized_data = sanitize_log_data(profile_data)
            logger.info(f"Updating profile for user_id: {user_id} with data: {sanitized_data}")

            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()

            logger.info(f"Successfully updated profile for user_id: {user_id}")
            return profile
    except ObjectDoesNotExist:
        logger.error(f"No profile found for user_id: {user_id}")
        raise


@log_exception(logger)
@timed_function(logger)
def create_user_profile(user_id, profile_data):
    """
    Create a new user profile with the provided data.

    This function creates a new user profile. It uses a database transaction to ensure
    data integrity and logs the operation.

    Args:
        user_id (int): The unique identifier of the user for whom the profile is being created.
        profile_data (dict): A dictionary containing the initial data for the profile.

    Returns:
        UserProfile: The newly created user profile.

    Raises:
        IntegrityError: If a profile for the given user_id already exists.
    """
    from apps.core.models import UserProfile

    logger.info(f"Attempting to create profile for user_id: {user_id}")
    try:
        with transaction.atomic():
            sanitized_data = sanitize_log_data(profile_data)
            logger.info(f"Creating profile for user_id: {user_id} with data: {sanitized_data}")

            profile = UserProfile.objects.create(user_id=user_id, **profile_data)

            logger.info(f"Successfully created profile for user_id: {user_id}")
            return profile
    except Exception as e:
        logger.error(f"Failed to create profile for user_id: {user_id}. Error: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def delete_user_profile(user_id):
    """
    Delete a user's profile.

    This function deletes an existing user profile. It uses a database transaction
    to ensure data integrity and logs the operation.

    Args:
        user_id (int): The unique identifier of the user whose profile is being deleted.

    Returns:
        bool: True if the profile was successfully deleted, False otherwise.

    Raises:
        ObjectDoesNotExist: If no profile is found for the given user_id.
    """
    from apps.core.models import UserProfile

    logger.info(f"Attempting to delete profile for user_id: {user_id}")
    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user_id=user_id)
            profile.delete()
            logger.info(f"Successfully deleted profile for user_id: {user_id}")
            return True
    except ObjectDoesNotExist:
        logger.error(f"No profile found for user_id: {user_id}")
        return False


def log_profile_access(func):
    """
    A decorator to log access to profile operations.

    This decorator wraps profile-related functions to log when they are accessed,
    providing an audit trail of profile operations.

    Args:
        func (callable): The function to be wrapped.

    Returns:
        callable: The wrapped function with added logging.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Accessing profile operation: {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


@log_profile_access
@log_exception(logger)
@timed_function(logger)
def get_profile_stats(user_id):
    """
    Retrieve statistics for a user's profile.

    This function calculates and returns various statistics related to a user's profile.
    It's useful for analytics and reporting purposes.

    Args:
        user_id (int): The unique identifier of the user.

    Returns:
        dict: A dictionary containing various profile statistics.

    Raises:
        ObjectDoesNotExist: If no profile is found for the given user_id.
    """
    from apps.coreapps.core.models import UserProfile

    logger.info(f"Calculating profile stats for user_id: {user_id}")
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        stats = {
            'profile_completeness': calculate_profile_completeness(profile),
            'last_updated': profile.updated_at,
            # Add more stats as needed
        }
        logger.info(f"Successfully calculated profile stats for user_id: {user_id}")
        return stats
    except ObjectDoesNotExist:
        logger.error(f"No profile found for user_id: {user_id}")
        raise


def calculate_profile_completeness(profile):
    """
    Calculate the completeness of a user's profile as a percentage.

    This helper function assesses how complete a user's profile is based on
    filled out fields. It's used by the get_profile_stats function.

    Args:
        profile (UserProfile): The user profile to assess.

    Returns:
        float: The profile completeness as a percentage.
    """
    total_fields = len(profile._meta.fields)
    filled_fields = sum(1 for f in profile._meta.fields if getattr(profile, f.name) not in [None, ''])
    return (filled_fields / total_fields) * 100


@transaction.atomic
def update_user_company_association(user, new_company):
    """
    Update a user's company association.

    This function removes the user from their old company's current employees,
    adds them to the old company's past employees, and then adds them to the
    new company's current employees (if a new company is provided).

    Args:
        user (User): The user whose company association is being updated.
        new_company (CompanyProfile or None): The new company the user is joining, or None if removing association.

    Returns:
        tuple: A tuple containing the old company (or None) and the new company (or None).
    """
    old_company = None

    # Check if user is currently associated with a company
    try:
        old_company = CompanyProfile.objects.get(current_employees=user)
        logger.info(f"User {user.id} is currently associated with company {old_company.id}")
    except CompanyProfile.DoesNotExist:
        logger.info(f"User {user.id} is not currently associated with any company")

    # Update company associations
    if old_company and old_company != new_company:
        try:
            old_company.current_employees.remove(user)
            old_company.past_employees.add(user)
            old_company.save()
            logger.info(f"User {user.id} removed from current employees and added to past employees of company {old_company.id}")
        except Exception as e:
            logger.error(f"Error updating old company association for user {user.id}: {str(e)}", exc_info=True)
            raise

    if new_company:
        try:
            new_company.current_employees.add(user)
            new_company.save()
            logger.info(f"User {user.id} added to current employees of company {new_company.id}")
        except Exception as e:
            logger.error(f"Error adding user {user.id} to new company {new_company.id}: {str(e)}", exc_info=True)
            raise
    else:
        logger.info(f"User {user.id} has removed their company association")

    logger.info(f"Company association updated for user {user.id}. Old company: {old_company.id if old_company else 'None'}, New company: {new_company.id if new_company else 'None'}")

    return old_company, new_company
