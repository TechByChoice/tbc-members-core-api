import logging
import time
from functools import wraps
from django.core.cache import cache
from django.conf import settings
import json

# Get logger
logger = logging.getLogger(__name__)


def log_cache_operation(operation):
    """
    Decorator to log cache operations with timing.

    Args:
        operation (str): The name of the cache operation being performed.

    Returns:
        function: The decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            logger.info(f"Cache {operation} operation completed in {end_time - start_time:.2f} seconds.")
            return result

        return wrapper

    return decorator


@log_cache_operation("set")
def set_cache(key, value, timeout=None):
    """
    Set a value in the cache.

    Args:
        key (str): The cache key.
        value (Any): The value to be cached.
        timeout (int, optional): The cache timeout in seconds. Defaults to None (uses default cache timeout).

    Returns:
        bool: True if the value was successfully cached, False otherwise.
    """
    try:
        serialized_value = json.dumps(value)
        success = cache.set(key, serialized_value, timeout)
        if success:
            logger.info(f"Successfully set cache for key: {key}")
        else:
            logger.warning(f"Failed to set cache for key: {key}")
        return success
    except Exception as e:
        logger.error(f"Error setting cache for key {key}: {str(e)}")
        return False


@log_cache_operation("get")
def get_cache(key, default=None):
    """
    Get a value from the cache.

    Args:
        key (str): The cache key.
        default (Any, optional): The default value to return if the key is not found. Defaults to None.

    Returns:
        Any: The cached value if found, otherwise the default value.
    """
    try:
        cached_value = cache.get(key)
        if cached_value is not None:
            deserialized_value = json.loads(cached_value)
            logger.info(f"Cache hit for key: {key}")
            return deserialized_value
        else:
            logger.info(f"Cache miss for key: {key}")
            return default
    except Exception as e:
        logger.error(f"Error getting cache for key {key}: {str(e)}")
        return default


@log_cache_operation("delete")
def delete_cache(key):
    """
    Delete a value from the cache.

    Args:
        key (str): The cache key to delete.

    Returns:
        bool: True if the key was successfully deleted, False otherwise.
    """
    try:
        cache.delete(key)
        logger.info(f"Successfully deleted cache for key: {key}")
        return True
    except Exception as e:
        logger.error(f"Error deleting cache for key {key}: {str(e)}")
        return False


@log_cache_operation("clear")
def clear_cache():
    """
    Clear the entire cache.

    Returns:
        bool: True if the cache was successfully cleared, False otherwise.
    """
    try:
        cache.clear()
        logger.info("Successfully cleared entire cache")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False


def cache_decorator(timeout=None):
    """
    Decorator to cache the result of a function.

    Args:
        timeout (int, optional): The cache timeout in seconds. Defaults to None (uses default cache timeout).

    Returns:
        function: The decorated function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique cache key based on the function name and arguments
            key = f"cache_decorator:{func.__name__}:{str(args)}:{str(kwargs)}"
            result = get_cache(key)

            if result is None:
                result = func(*args, **kwargs)
                set_cache(key, result, timeout)
                logger.info(f"Cached result for function: {func.__name__}")
            else:
                logger.info(f"Retrieved cached result for function: {func.__name__}")

            return result

        return wrapper

    return decorator


def get_cache_key(*args, **kwargs):
    """
    Generate a unique cache key based on the provided arguments.

    Args:
        *args: Positional arguments to include in the key.
        **kwargs: Keyword arguments to include in the key.

    Returns:
        str: A unique cache key.
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


def cache_health_check():
    """
    Perform a health check on the cache system.

    Returns:
        bool: True if the cache is functioning correctly, False otherwise.
    """
    try:
        test_key = "cache_health_check"
        test_value = "test_value"

        # Test setting a value
        set_cache(test_key, test_value)

        # Test getting the value
        retrieved_value = get_cache(test_key)

        # Test deleting the value
        delete_cache(test_key)

        # Verify the operations
        if retrieved_value == test_value and get_cache(test_key) is None:
            logger.info("Cache health check passed")
            return True
        else:
            logger.warning("Cache health check failed: unexpected values")
            return False
    except Exception as e:
        logger.error(f"Cache health check failed with error: {str(e)}")
        return False


# Initialize cache on module load
try:
    cache_backend = settings.CACHES['default']['BACKEND']
    logger.info(f"Initializing cache with backend: {cache_backend}")
    cache_health_check()
except Exception as e:
    logger.error(f"Failed to initialize cache: {str(e)}")
