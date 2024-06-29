import json
import csv
import logging
from functools import wraps
from typing import Any, Dict, List, Union
from decimal import Decimal

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
