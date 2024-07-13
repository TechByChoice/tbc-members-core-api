import csv
import json
import re
from decimal import Decimal
from typing import Any, Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.utils.text import slugify

from apps.core.models import UserProfile
# Import the custom logging utilities
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

# Initialize logger
logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def serialize_data(data: Any, format: str = 'json') -> str:
    """
    Serialize data to a specified format.

    This function takes any Python data structure and serializes it to the specified format.
    Currently supported formats are 'json' and 'csv'.

    Args:
        data (Any): The data to be serialized.
        format (str, optional): The output format. Defaults to 'json'.

    Returns:
        str: The serialized data as a string.

    Raises:
        ValueError: If an unsupported format is specified.

    Example:
        >>> data = {'name': 'John', 'age': 30}
        >>> serialize_data(data, 'json')
        '{"name": "John", "age": 30}'
    """
    logger.info(f"Serializing data to {format} format")

    if format == 'json':
        return json.dumps(data)
    elif format == 'csv':
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("CSV serialization requires a list of dictionaries")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    else:
        raise ValueError(f"Unsupported serialization format: {format}")


@log_exception(logger)
@timed_function(logger)
def deserialize_data(data: str, format: str = 'json') -> Any:
    """
    Deserialize data from a specified format.

    This function takes a string in the specified format and deserializes it into a Python data structure.
    Currently supported formats are 'json' and 'csv'.

    Args:
        data (str): The serialized data string.
        format (str, optional): The input format. Defaults to 'json'.

    Returns:
        Any: The deserialized Python data structure.

    Raises:
        ValueError: If an unsupported format is specified.

    Example:
        >>> json_data = '{"name": "John", "age": 30}'
        >>> deserialize_data(json_data, 'json')
        {'name': 'John', 'age': 30}
    """
    logger.info(f"Deserializing data from {format} format")

    if format == 'json':
        return json.loads(data)
    elif format == 'csv':
        reader = csv.DictReader(io.StringIO(data))
        return list(reader)
    else:
        raise ValueError(f"Unsupported deserialization format: {format}")


@log_exception(logger)
def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a specified schema.

    This function checks if the provided data conforms to the given schema.
    The schema should be a dictionary where keys are field names and values are types or validation functions.

    Args:
        data (Dict[str, Any]): The data to be validated.
        schema (Dict[str, Any]): The schema to validate against.

    Returns:
        bool: True if the data is valid, False otherwise.

    Example:
        >>> schema = {'name': str, 'age': lambda x: isinstance(x, int) and x > 0}
        >>> validate_data({'name': 'John', 'age': 30}, schema)
        True
        >>> validate_data({'name': 'John', 'age': -5}, schema)
        False
    """
    logger.info("Validating data against schema")
    sanitized_data = sanitize_log_data(data)
    logger.debug(f"Validating data: {sanitized_data}")

    for field, validator in schema.items():
        if field not in data:
            logger.warning(f"Field '{field}' is missing in the data")
            return False
        if callable(validator):
            if not validator(data[field]):
                logger.warning(f"Validation failed for field '{field}'")
                return False
        elif not isinstance(data[field], validator):
            logger.warning(f"Type mismatch for field '{field}'. Expected {validator}, got {type(data[field])}")
            return False
    return True


@log_exception(logger)
def anonymize_data(data: Dict[str, Any], fields_to_anonymize: List[str]) -> Dict[str, Any]:
    """
    Anonymize sensitive fields in the data.

    This function replaces the values of specified fields with anonymized versions.

    Args:
        data (Dict[str, Any]): The original data.
        fields_to_anonymize (List[str]): List of field names to anonymize.

    Returns:
        Dict[str, Any]: The data with specified fields anonymized.

    Example:
        >>> data = {'name': 'John Doe', 'email': 'john@example.com', 'age': 30}
        >>> anonymize_data(data, ['name', 'email'])
        {'name': '****', 'email': '****', 'age': 30}
    """
    logger.info(f"Anonymizing fields: {fields_to_anonymize}")

    anonymized_data = data.copy()
    for field in fields_to_anonymize:
        if field in anonymized_data:
            anonymized_data[field] = '****'
    return anonymized_data


@log_exception(logger)
@timed_function(logger)
def check_data_integrity(data: Any, checksum: str) -> bool:
    """
    Check the integrity of data using a checksum.

    This function verifies if the provided data matches the given checksum.

    Args:
        data (Any): The data to check.
        checksum (str): The expected checksum.

    Returns:
        bool: True if the data integrity is verified, False otherwise.

    Example:
        >>> import hashlib
        >>> data = "Hello, World!"
        >>> checksum = hashlib.md5(data.encode()).hexdigest()
        >>> check_data_integrity(data, checksum)
        True
    """
    logger.info("Checking data integrity")

    import hashlib
    computed_checksum = hashlib.md5(str(data).encode()).hexdigest()
    is_valid = computed_checksum == checksum
    logger.info(f"Data integrity check {'passed' if is_valid else 'failed'}")
    return is_valid


@log_exception(logger)
@timed_function(logger)
def import_data(file_path: str, format: str = 'csv') -> List[Dict[str, Any]]:
    """
    Import data from a file.

    This function reads data from a file and returns it as a list of dictionaries.
    Currently supported formats are 'csv' and 'json'.

    Args:
        file_path (str): The path to the file to import.
        format (str, optional): The format of the file. Defaults to 'csv'.

    Returns:
        List[Dict[str, Any]]: The imported data as a list of dictionaries.

    Raises:
        ValueError: If an unsupported format is specified.

    Example:
        >>> import_data('data.csv', 'csv')
        [{'name': 'John', 'age': '30'}, {'name': 'Jane', 'age': '25'}]
    """
    logger.info(f"Importing data from {file_path} in {format} format")

    if format == 'csv':
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            return list(reader)
    elif format == 'json':
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        raise ValueError(f"Unsupported import format: {format}")


@log_exception(logger)
@timed_function(logger)
def export_data(data: List[Dict[str, Any]], file_path: str, format: str = 'csv') -> None:
    """
    Export data to a file.

    This function writes data to a file in the specified format.
    Currently supported formats are 'csv' and 'json'.

    Args:
        data (List[Dict[str, Any]]): The data to export.
        file_path (str): The path where the file should be saved.
        format (str, optional): The format to use for export. Defaults to 'csv'.

    Raises:
        ValueError: If an unsupported format is specified.

    Example:
        >>> data = [{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}]
        >>> export_data(data, 'output.csv', 'csv')
    """
    logger.info(f"Exporting data to {file_path} in {format} format")

    if format == 'csv':
        with open(file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    elif format == 'json':
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
    else:
        raise ValueError(f"Unsupported export format: {format}")


@log_exception(logger)
def convert_currency(amount: Union[int, float, Decimal], from_currency: str, to_currency: str) -> Decimal:
    """
    Convert an amount from one currency to another.

    This function uses predefined exchange rates to convert currencies.
    Note: In a production environment, you would typically use a third-party service or API for up-to-date exchange rates.

    Args:
        amount (Union[int, float, Decimal]): The amount to convert.
        from_currency (str): The currency code to convert from.
        to_currency (str): The currency code to convert to.

    Returns:
        Decimal: The converted amount.

    Raises:
        ValueError: If an unsupported currency is specified.

    Example:
        >>> convert_currency(100, 'USD', 'EUR')
        Decimal('84.75')
    """
    logger.info(f"Converting {amount} from {from_currency} to {to_currency}")

    # Example exchange rates (replace with actual rates or API call)
    exchange_rates = {
        'USD': {'EUR': Decimal('0.8475'), 'GBP': Decimal('0.7246')},
        'EUR': {'USD': Decimal('1.1799'), 'GBP': Decimal('0.8555')},
        'GBP': {'USD': Decimal('1.3800'), 'EUR': Decimal('1.1688')}
    }

    if from_currency not in exchange_rates or to_currency not in exchange_rates[from_currency]:
        raise ValueError(f"Unsupported currency conversion: {from_currency} to {to_currency}")

    rate = exchange_rates[from_currency][to_currency]
    converted_amount = Decimal(str(amount)) * rate
    return converted_amount.quantize(Decimal('0.01'))


def update_review_token_total(user, direction):
    """
    Update the user's review token total.

    :param user: User object
    :param direction: Boolean, True to increase tokens, False to decrease
    :return: Dict with updated token count or error message
    """
    try:
        token_change = 1 if direction else -1

        # Prevent negative token count
        if not direction and user.company_review_tokens <= 0:
            logger.warning(f"Attempted to decrease tokens below zero for user {user.id}")
            return {"error": "Cannot decrease tokens below zero", "data": user.company_review_tokens}

        user.company_review_tokens += token_change

        # Update review access status
        if user.company_review_tokens == 0:
            user.is_company_review_access_active = False
        elif user.company_review_tokens > 0 and not user.is_company_review_access_active:
            user.is_company_review_access_active = True

        user.save()

        logger.info(f"Updated review tokens for user {user.id}. New total: {user.company_review_tokens}")
        return True

    except Exception as e:
        logger.error(f"Error updating review tokens for user {user.id}: {str(e)}")
        return False


class UserDemoService:
    @staticmethod
    def get_user_demo(user):
        """
        Fetch user demographic data.

        Args:
            user (User): The user object.

        Returns:
            dict: A dictionary containing user demographic data or error information.
        """
        try:
            user_demo_data = UserProfile.objects.filter(user=user).annotate(
                sexuality_name=F('identity_sexuality__name'),
                gender_name=F('identity_gender__name'),
                ethic_name=F('identity_ethic__name'),
                pronouns_name=F('identity_pronouns__name'),
            ).values(
                'sexuality_name',
                'gender_name',
                'ethic_name',
                'pronouns_name',
                "disability",
                "care_giver",
                "veteran_status",
            )

            user_account_data = {
                "is_company_review_access_active": user.is_company_review_access_active,
                "company_review_tokens": user.company_review_tokens,
            }

            user_data = {
                "user_demo": list(user_demo_data),
                "user_account": user_account_data,
                "user_id": user.id,
                "status": True
            }

            logger.info(f"Successfully retrieved demo data for user {user.id}")
            return user_data

        except ObjectDoesNotExist:
            logger.error(f"UserProfile does not exist for user {user.id}")
            return {"status": False, "error": "UserProfile not found"}
        except Exception as e:
            logger.exception(f"Unexpected error retrieving user data for {user.id}. Error: {str(e)}")
            return {"status": False, "error": "An unexpected error occurred"}

    @staticmethod
    def sanitize_user_data(user_data):
        """
        Sanitize user data to remove sensitive information.

        Args:
            user_data (dict): The raw user data.

        Returns:
            dict: Sanitized user data.
        """
        sensitive_fields = ['email', 'phone_number', 'social_security_number']

        for field in sensitive_fields:
            if field in user_data:
                del user_data[field]

        return user_data

    @staticmethod
    def validate_user_data(user_data):
        """
        Validate user data to ensure all required fields are present.

        Args:
            user_data (dict): The user data to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        required_fields = ['user_id', 'user_demo', 'user_account']

        for field in required_fields:
            if field not in user_data:
                logger.error(f"Missing required field: {field}")
                return False

        return True


def get_user_demo(user):
    """
    Wrapper function to get user demo data.

    Args:
        user (User): The user object.

    Returns:
        dict: A dictionary containing user demographic data or error information.
    """
    user_demo_service = UserDemoService()
    user_data = user_demo_service.get_user_demo(user)

    if user_data['status']:
        user_data = user_demo_service.sanitize_user_data(user_data)
        if not user_demo_service.validate_user_data(user_data):
            return {"status": False, "error": "Invalid user data"}

    return user_data


def normalize_name(name):
    """
    Normalize a given name by removing 'Add "..."' pattern, converting to lowercase,
    removing spaces and special characters.
    """

    # Remove 'Add "..."' pattern
    cleaned_name = re.sub(r'^Add\s*"(.+)"$', r'\1', name.strip())
    normalized_name = slugify(cleaned_name.lower().replace(' ', ''))

    return cleaned_name, normalized_name


def get_or_create_normalized(model_class, name, extra_fields=None):
    """
    Get or create a model instance with a normalized name.

    :param model_class: The model class to use (e.g., Department, Skill)
    :param name: The name to normalize and use for get_or_create
    :param extra_fields: A dictionary of extra fields to use when creating a new instance
    :return: A tuple (object, created) where object is the retrieved or created instance
             and created is a boolean specifying whether a new instance was created
    """
    # Remove 'Add "..."' pattern
    clean_name, normalized_name = normalize_name(name)

    defaults = {'normalized_name': normalized_name}
    if extra_fields:
        defaults.update(extra_fields)

    obj, created = model_class.objects.get_or_create(
        name=clean_name,
        defaults=defaults
    )

    return obj, created
