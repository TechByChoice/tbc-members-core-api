import logging
from functools import wraps
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def authenticate_user(username, password):
    """
    Authenticate a user with their username and password.

    This function attempts to authenticate a user and logs the attempt.
    It sanitizes the input data before logging to ensure sensitive information is not exposed.

    Args:
        username (str): The user's username or email.
        password (str): The user's password.

    Returns:
        User: The authenticated user object if successful, None otherwise.

    Raises:
        AuthenticationFailed: If authentication fails.
    """
    sanitized_data = sanitize_log_data({'username': username, 'password': password})
    logger.info(f"Attempting to authenticate user: {sanitized_data['username']}")

    user = authenticate(username=username, password=password)

    if user is not None:
        logger.info(f"User {username} authenticated successfully")
        return user
    else:
        logger.warning(f"Failed authentication attempt for user: {username}")
        raise AuthenticationFailed("Invalid username or password")


@log_exception(logger)
@timed_function(logger)
def generate_auth_token(user):
    """
    Generate or retrieve an authentication token for a user.

    This function creates a new token if one doesn't exist, or returns the existing one.

    Args:
        user (User): The user object for which to generate/retrieve the token.

    Returns:
        str: The authentication token.
    """
    logger.info(f"Generating auth token for user: {user.username}")
    token, created = Token.objects.get_or_create(user=user)

    if created:
        logger.info(f"New auth token created for user: {user.username}")
    else:
        logger.info(f"Existing auth token retrieved for user: {user.username}")

    return token.key


@log_exception(logger)
def verify_auth_token(token):
    """
    Verify the validity of an authentication token.

    This function checks if the provided token exists and is associated with a user.

    Args:
        token (str): The authentication token to verify.

    Returns:
        User: The user associated with the token if valid.

    Raises:
        AuthenticationFailed: If the token is invalid or expired.
    """
    logger.info("Verifying auth token")
    try:
        token_obj = Token.objects.get(key=token)
        logger.info(f"Auth token verified for user: {token_obj.user.username}")
        return token_obj.user
    except Token.DoesNotExist:
        logger.warning("Invalid auth token provided")
        raise AuthenticationFailed("Invalid or expired token")


def require_permissions(*permissions):
    """
    Decorator to check if a user has the required permissions.

    This decorator can be applied to view functions to ensure the user has all the specified permissions.

    Args:
        *permissions: Variable number of permission strings to check.

    Returns:
        function: The decorated function.

    Raises:
        PermissionDenied: If the user lacks any of the required permissions.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            logger.info(f"Checking permissions: {permissions} for user: {request.user.username}")
            if not request.user.has_perms(permissions):
                logger.warning(
                    f"Permission denied for user: {request.user.username}. Required permissions: {permissions}")
                raise PermissionDenied("You do not have the required permissions to perform this action.")
            logger.info(f"Permissions check passed for user: {request.user.username}")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


@log_exception(logger)
@timed_function(logger)
def generate_password_reset_token(user):
    """
    Generate a password reset token for a user.

    This function creates a unique token that can be used for password reset functionality.

    Args:
        user (User): The user object for which to generate the reset token.

    Returns:
        str: The generated password reset token.
    """
    logger.info(f"Generating password reset token for user: {user.username}")
    token = default_token_generator.make_token(user)
    logger.info(f"Password reset token generated for user: {user.username}")
    return token


@log_exception(logger)
@timed_function(logger)
def verify_password_reset_token(user, token):
    """
    Verify the validity of a password reset token.

    This function checks if the provided token is valid for the given user.

    Args:
        user (User): The user object for which to verify the token.
        token (str): The password reset token to verify.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    logger.info(f"Verifying password reset token for user: {user.username}")
    is_valid = default_token_generator.check_token(user, token)
    if is_valid:
        logger.info(f"Valid password reset token for user: {user.username}")
    else:
        logger.warning(f"Invalid password reset token for user: {user.username}")
    return is_valid