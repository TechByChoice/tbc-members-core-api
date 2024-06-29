import logging
from django.db import transaction
from functools import wraps
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def atomic_transaction(func):
    """
    A decorator to wrap a function in a database transaction.

    This decorator ensures that all database operations within the decorated function
    are executed as a single atomic transaction. If any exception occurs during the
    execution, all database changes will be rolled back.

    Args:
        func (callable): The function to be wrapped in a transaction.

    Returns:
        callable: A wrapped function that executes within a database transaction.

    Example:
        @atomic_transaction
        def create_user_profile(user_data, profile_data):
            user = User.objects.create(**user_data)
            Profile.objects.create(user=user, **profile_data)

    Note:
        This decorator logs the start and end of each transaction, as well as any
        exceptions that occur during the transaction.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Starting transaction for function: {func.__name__}")
        try:
            with transaction.atomic():
                result = func(*args, **kwargs)
            logger.info(f"Successfully completed transaction for function: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Transaction failed for function {func.__name__}: {str(e)}")
            raise

    return wrapper


@log_exception(logger)
@timed_function(logger)
def safe_bulk_create(model, objects, batch_size=100):
    """
    Safely create multiple objects in the database using bulk_create.

    This function creates multiple objects in the database using Django's bulk_create
    method. It wraps the operation in a transaction to ensure atomicity and logs
    the process for monitoring and debugging purposes.

    Args:
        model (Model): The Django model class to create objects for.
        objects (list): A list of model instances to create.
        batch_size (int, optional): The number of objects to create in each batch.
            Defaults to 100.

    Returns:
        list: The list of created objects.

    Raises:
        Exception: If any error occurs during the bulk create operation.

    Example:
        users = [User(username=f"user_{i}") for i in range(1000)]
        created_users = safe_bulk_create(User, users, batch_size=200)
    """
    logger.info(f"Starting bulk create for {len(objects)} {model.__name__} objects")
    try:
        with transaction.atomic():
            created_objects = model.objects.bulk_create(objects, batch_size=batch_size)
        logger.info(f"Successfully created {len(created_objects)} {model.__name__} objects")
        return created_objects
    except Exception as e:
        logger.error(f"Bulk create failed for {model.__name__}: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def safe_bulk_update(model, objects, fields, batch_size=100):
    """
    Safely update multiple objects in the database using bulk_update.

    This function updates multiple objects in the database using Django's bulk_update
    method. It wraps the operation in a transaction to ensure atomicity and logs
    the process for monitoring and debugging purposes.

    Args:
        model (Model): The Django model class to update objects for.
        objects (list): A list of model instances to update.
        fields (list): A list of field names to update.
        batch_size (int, optional): The number of objects to update in each batch.
            Defaults to 100.

    Returns:
        int: The number of updated objects.

    Raises:
        Exception: If any error occurs during the bulk update operation.

    Example:
        users = User.objects.filter(is_active=True)
        for user in users:
            user.is_active = False
        updated_count = safe_bulk_update(User, users, ['is_active'], batch_size=200)
    """
    logger.info(f"Starting bulk update for {len(objects)} {model.__name__} objects")
    try:
        with transaction.atomic():
            updated_count = model.objects.bulk_update(objects, fields, batch_size=batch_size)
        logger.info(f"Successfully updated {updated_count} {model.__name__} objects")
        return updated_count
    except Exception as e:
        logger.error(f"Bulk update failed for {model.__name__}: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def safe_get_or_create(model, defaults=None, **kwargs):
    """
    Safely get or create an object in the database.

    This function attempts to retrieve an object from the database, and if it
    doesn't exist, creates it. It wraps the operation in a transaction to ensure
    atomicity and logs the process for monitoring and debugging purposes.

    Args:
        model (Model): The Django model class to get or create an object for.
        defaults (dict, optional): A dictionary of default values to use when
            creating the object. Defaults to None.
        **kwargs: Keyword arguments used to look up the object.

    Returns:
        tuple: A tuple (object, created), where object is the retrieved or created
               object and created is a boolean specifying whether a new object was created.

    Raises:
        Exception: If any error occurs during the get or create operation.

    Example:
        user, created = safe_get_or_create(User, defaults={'is_active': True}, username='newuser')
    """
    logger.info(f"Attempting to get or create {model.__name__} object")
    try:
        with transaction.atomic():
            obj, created = model.objects.get_or_create(defaults=defaults, **kwargs)
        if created:
            logger.info(f"Created new {model.__name__} object")
        else:
            logger.info(f"Retrieved existing {model.__name__} object")
        return obj, created
    except Exception as e:
        logger.error(f"Get or create failed for {model.__name__}: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def safe_update_or_create(model, defaults=None, **kwargs):
    """
    Safely update or create an object in the database.

    This function attempts to update an existing object in the database, and if it
    doesn't exist, creates it. It wraps the operation in a transaction to ensure
    atomicity and logs the process for monitoring and debugging purposes.

    Args:
        model (Model): The Django model class to update or create an object for.
        defaults (dict, optional): A dictionary of values to use when updating or
            creating the object. Defaults to None.
        **kwargs: Keyword arguments used to look up the object.

    Returns:
        tuple: A tuple (object, created), where object is the updated or created
               object and created is a boolean specifying whether a new object was created.

    Raises:
        Exception: If any error occurs during the update or create operation.

    Example:
        user, created = safe_update_or_create(User, defaults={'is_active': True}, username='existinguser')
    """
    logger.info(f"Attempting to update or create {model.__name__} object")
    try:
        with transaction.atomic():
            obj, created = model.objects.update_or_create(defaults=defaults, **kwargs)
        if created:
            logger.info(f"Created new {model.__name__} object")
        else:
            logger.info(f"Updated existing {model.__name__} object")
        return obj, created
    except Exception as e:
        logger.error(f"Update or create failed for {model.__name__}: {str(e)}")
        raise