import re
import logging
from functools import wraps
from urllib.parse import urlparse, urlunparse

# Import the custom logging utilities
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

# Get a logger for this module
logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def prepend_https_if_not_empty(url):
    """
    Prepend 'https://' to a URL if it's not empty and doesn't already start with 'http://' or 'https://'.

    This function ensures that all non-empty URLs have the 'https://' scheme. If the URL is empty or None,
    it returns an empty string. If the URL already starts with 'http://' or 'https://', it remains unchanged.

    Args:
        url (str): The URL to process.

    Returns:
        str: The processed URL with 'https://' prepended if necessary, or an empty string if the input was empty or None.

    Examples:
        >>> prepend_https_if_not_empty('example.com')
        'https://example.com'
        >>> prepend_https_if_not_empty('https://example.com')
        'https://example.com'
        >>> prepend_https_if_not_empty('http://example.com')
        'http://example.com'
        >>> prepend_https_if_not_empty('')
        ''
        >>> prepend_https_if_not_empty(None)
        ''
    """
    logger.info(f"Processing URL: {sanitize_log_data({'url': url})}")

    if not url:
        logger.debug("Empty URL provided, returning empty string")
        return ''

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        logger.debug(f"Prepended 'https://' to URL: {sanitize_log_data({'url': url})}")

    return url


@log_exception(logger)
@timed_function(logger)
def normalize_social_media_url(url, platform):
    """
    Normalize a social media URL for a given platform.

    This function takes a URL and a social media platform name, and returns a normalized version of the URL
    that follows the standard format for that platform. It handles common variations in how users might input
    their social media profile URLs.

    Args:
        url (str): The social media URL to normalize.
        platform (str): The name of the social media platform (e.g., 'facebook', 'twitter', 'linkedin', 'instagram').

    Returns:
        str: The normalized social media URL.

    Raises:
        ValueError: If an unsupported social media platform is provided.

    Examples:
        >>> normalize_social_media_url('facebook.com/johndoe', 'facebook')
        'https://www.facebook.com/johndoe'
        >>> normalize_social_media_url('@johndoe', 'twitter')
        'https://twitter.com/johndoe'
        >>> normalize_social_media_url('linkedin.com/in/johndoe', 'linkedin')
        'https://www.linkedin.com/in/johndoe'
    """
    logger.info(f"Normalizing social media URL: {sanitize_log_data({'url': url, 'platform': platform})}")

    url = url.strip().lower()

    if platform == 'facebook':
        pattern = r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/(.+)'
        match = re.match(pattern, url)
        if match:
            username = match.group(1)
        else:
            username = url.lstrip('@')
        normalized_url = f'https://www.facebook.com/{username}'

    elif platform == 'twitter':
        pattern = r'(?:https?:\/\/)?(?:www\.)?twitter\.com\/(.+)'
        match = re.match(pattern, url)
        if match:
            username = match.group(1)
        else:
            username = url.lstrip('@')
        normalized_url = f'https://twitter.com/{username}'

    elif platform == 'linkedin':
        pattern = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/(.+)'
        match = re.match(pattern, url)
        if match:
            username = match.group(1)
        else:
            username = url.lstrip('@')
        normalized_url = f'https://www.linkedin.com/in/{username}'

    elif platform == 'instagram':
        pattern = r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(.+)'
        match = re.match(pattern, url)
        if match:
            username = match.group(1)
        else:
            username = url.lstrip('@')
        normalized_url = f'https://www.instagram.com/{username}'

    else:
        logger.error(f"Unsupported social media platform: {platform}")
        raise ValueError(f"Unsupported social media platform: {platform}")

    logger.debug(f"Normalized URL: {sanitize_log_data({'normalized_url': normalized_url})}")
    return normalized_url


@log_exception(logger)
@timed_function(logger)
def extract_username_from_url(url, platform):
    """
    Extract the username from a social media URL for a given platform.

    This function takes a URL and a social media platform name, and returns the username
    associated with that URL. It can handle various formats of URLs for different platforms.

    Args:
        url (str): The social media URL to extract the username from.
        platform (str): The name of the social media platform (e.g., 'facebook', 'twitter', 'linkedin', 'instagram').

    Returns:
        str: The extracted username, or None if no username could be extracted.

    Raises:
        ValueError: If an unsupported social media platform is provided.

    Examples:
        >>> extract_username_from_url('https://www.facebook.com/johndoe', 'facebook')
        'johndoe'
        >>> extract_username_from_url('https://twitter.com/johndoe', 'twitter')
        'johndoe'
        >>> extract_username_from_url('https://www.linkedin.com/in/john-doe-123456', 'linkedin')
        'john-doe-123456'
    """
    logger.info(f"Extracting username from URL: {sanitize_log_data({'url': url, 'platform': platform})}")

    normalized_url = normalize_social_media_url(url, platform)
    parsed_url = urlparse(normalized_url)

    if platform == 'facebook':
        username = parsed_url.path.strip('/')
    elif platform == 'twitter':
        username = parsed_url.path.strip('/').lstrip('@')
    elif platform == 'linkedin':
        username = parsed_url.path.strip('/').lstrip('in/')
    elif platform == 'instagram':
        username = parsed_url.path.strip('/')
    else:
        logger.error(f"Unsupported social media platform: {platform}")
        raise ValueError(f"Unsupported social media platform: {platform}")

    logger.debug(f"Extracted username: {sanitize_log_data({'username': username})}")
    return username if username else None


@log_exception(logger)
@timed_function(logger)
def validate_social_media_url(url, platform):
    """
    Validate a social media URL for a given platform.

    This function checks if the provided URL is a valid social media profile URL for the specified platform.
    It uses regular expressions to match the URL against the expected format for each platform.

    Args:
        url (str): The social media URL to validate.
        platform (str): The name of the social media platform (e.g., 'facebook', 'twitter', 'linkedin', 'instagram').

    Returns:
        bool: True if the URL is valid for the given platform, False otherwise.

    Raises:
        ValueError: If an unsupported social media platform is provided.

    Examples:
        >>> validate_social_media_url('https://www.facebook.com/johndoe', 'facebook')
        True
        >>> validate_social_media_url('https://twitter.com/johndoe', 'twitter')
        True
        >>> validate_social_media_url('https://www.linkedin.com/in/john-doe-123456', 'linkedin')
        True
        >>> validate_social_media_url('https://www.instagram.com/johndoe', 'instagram')
        True
        >>> validate_social_media_url('https://www.example.com', 'facebook')
        False
    """
    logger.info(f"Validating social media URL: {sanitize_log_data({'url': url, 'platform': platform})}")

    patterns = {
        'facebook': r'^https?:\/\/(www\.)?facebook\.com\/[a-zA-Z0-9.]+\/?$',
        'twitter': r'^https?:\/\/(www\.)?twitter\.com\/[a-zA-Z0-9_]+\/?$',
        'linkedin': r'^https?:\/\/(www\.)?linkedin\.com\/in\/[\w-]+\/?$',
        'instagram': r'^https?:\/\/(www\.)?instagram\.com\/[a-zA-Z0-9_.]+\/?$'
    }

    if platform not in patterns:
        logger.error(f"Unsupported social media platform: {platform}")
        raise ValueError(f"Unsupported social media platform: {platform}")

    is_valid = bool(re.match(patterns[platform], url))
    logger.debug(f"URL validation result: {sanitize_log_data({'is_valid': is_valid})}")
    return is_valid


def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain
