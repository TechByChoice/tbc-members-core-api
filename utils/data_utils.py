import json
import csv
import logging
from functools import wraps
from typing import Any, Dict, List, Union
from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.company.models import CompanyProfile, SalaryRange, Skill, Department, Roles, CompanyTypes
from apps.core.models import UserProfile, PronounsIdentities, EthicIdentities, GenderIdentities, SexualIdentities
from apps.core.serializers import UserProfileSerializer
from apps.member.models import MemberProfile
from .errors import CustomException
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


def get_id_or_create(model, name):
    obj, created = model.objects.get_or_create(name=name)
    return obj.id


def update_user(current_user, user_data):
    """
    Create or update a user instance based on the provided user_data.

    :param current_user: The user instance to update.
    :param user_data: A dictionary containing the data for the user.
    :return: The created or updated user instance.
    """
    try:
        # Assuming you're partially updating an existing user
        user_serializer = UserProfileSerializer(
            instance=current_user, data=user_data, partial=True
        )

        # Validate the user data
        user_serializer.is_valid(raise_exception=True)

        # Save the user object and return it
        return user_serializer.save()
    except serializers.ValidationError as e:
        # Handle validation errors, e.g., return a meaningful error message or raise an exception
        print(f"Validation error while creating/updating user: {e}")
        raise
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error while creating/updating user: {e}")
        raise


def update_user_profile(user, profile_data):
    """
    Update a user profile.

    This function will create a new UserProfile or update an existing one based on the provided user. It will set fields
    for identity_sexuality, identity_gender, identity_ethic, identity_pronouns, and other provided profile data.

    Args:
        user (CustomUser): The user object for whom the profile is being created or updated.
        profile_data (dict): A dictionary containing profile data.

    Returns:
        UserProfile: The created or updated UserProfile object.

    Raises:
        CustomException: If there's any issue in creating or updating the UserProfile or related objects.
    """
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist as e:
        # Log the exception and raise a custom exception for the caller to handle
        print(f"UserProfile does not exist for user {user.id}: {e}")
        raise CustomException(f"Failed to create or update UserProfile: {str(e)}")

    # Process and set many-to-many fields
    if "identity_sexuality" in profile_data and not profile_data[
                                                        "identity_sexuality"
                                                    ] == [""]:
        sexuality_instances = process_identity_field(
            profile_data["identity_sexuality"], SexualIdentities
        )
        profile_data["identity_sexuality"] = sexuality_instances
    else:
        del profile_data["identity_sexuality"]

    if "identity_gender" in profile_data and not profile_data["identity_gender"] == [
        ""
    ]:
        gender_instances = process_identity_field(
            profile_data["identity_gender"], GenderIdentities
        )
        profile_data["identity_gender"] = gender_instances
    else:
        del profile_data["identity_gender"]

    if "identity_ethic" in profile_data and not profile_data["identity_ethic"] == [""]:
        ethic_instances = process_identity_field(
            profile_data["identity_ethic"], EthicIdentities
        )
        profile_data["identity_ethic"] = ethic_instances
    else:
        del profile_data["identity_ethic"]

    if "identity_pronouns" in profile_data and not profile_data[
                                                       "identity_pronouns"
                                                   ] == [""]:
        pronouns_instances = process_identity_field(
            profile_data["identity_pronouns"], PronounsIdentities
        )
        profile_data["identity_pronouns"] = pronouns_instances
    else:
        del profile_data["identity_pronouns"]

    # For fields that are not many-to-many relationships, update them directly
    try:
        for field, value in profile_data.items():
            if field not in [
                "identity_sexuality",
                "identity_gender",
                "identity_ethic",
                "identity_pronouns",
            ]:
                setattr(user_profile, field, value)
            if "photo" in field:
                user_profile.photo = value
        try:
            user_profile.set_tbc_program_interest(profile_data["tbc_program_interest"])
            user_profile.postal_code = profile_data["postal_code"]
        except Exception as e:
            print(f"Error trying to update items: {e}")
        try:
            user_profile.save(force_update=True)
            print("UserProfile saved successfully.")
        except Exception as e:
            print(f"Error saving UserProfile: {e}")

        # Verify the save operation by fetching the profile again
        try:
            updated_profile = UserProfile.objects.get(user=user)
            print(f"Updated postal code: {updated_profile.postal_code}")
        except UserProfile.DoesNotExist:
            print("UserProfile does not exist.")

        return user_profile
    except Exception as e:
        print(f"Error updating user_profile: {e}")


def process_identity_field(identity_list, model):
    """
    Process and validate name-related fields before setting them in the UserProfile.

    This function takes a list of name names or identifiers, ensures that these identities
    are present in the database (creating them if necessary), and returns a queryset
    or list of Identity model instances.

    Args:
    identity_list (list): A list of name names or identifiers.
    model (Django model class): The model class for the name (e.g., SexualIdentities, GenderIdentities).

    Returns:
    QuerySet: A QuerySet of Identity instances to be associated with the UserProfile.

    Raises:
    ValueError: If any of the identities are invalid or cannot be processed.
    """
    identity_instances = []

    for identity_name in identity_list:
        # Validate or process identity_name here (e.g., check if it's a non-empty string)
        if not identity_name or not isinstance(identity_name, str):
            raise ValueError(f"Invalid name: {identity_name}")

        # Try to get the name by name, or create it if it doesn't exist
        identity, created = model.objects.get_or_create(name=identity_name.strip())

        # Optionally, handle the case where the name creation failed (if get_or_create does not meet your needs)
        if not identity:
            raise ValueError(
                f"Failed to create or retrieve name with name: {identity_name}"
            )

        identity_instances.append(identity)

    return identity_instances


def extract_talent_data(data, files):
    talent_data = {
        "tech_journey": data.get("years_of_experience"),
        "is_talent_status": data.get("talent_status") == "Yes",
        "company_types": [get_id_or_create(CompanyTypes, ct) for ct in data.getlist("company_types", [])],
        "department": [get_id_or_create(Department, dept) for dept in data.getlist("job_department", [])],
        "role": [get_id_or_create(Roles, role) for role in data.getlist("job_roles", [])],
        "skills": [get_id_or_create(Skill, skill) for skill in data.getlist("job_skills", [])],
        "min_compensation": get_id_or_create(SalaryRange, data.get("min_compensation")),
        "max_compensation": get_id_or_create(SalaryRange, data.get("max_compensation")),
        "resume": files.get("resume"),
    }
    return talent_data


def extract_profile_id_data(data, files):
    profile_data = {
        "linkedin": data.get("linkedin"),
        "instagram": data.get("instagram"),
        "github": data.get("github"),
        "twitter": data.get("twitter"),
        "youtube": data.get("youtube"),
        "personal": data.get("personal"),
        "identity_sexuality": [get_id_or_create(SexualIdentities, si) for si in data.getlist("identity_sexuality", [])],
        "identity_gender": [get_id_or_create(GenderIdentities, gi) for gi in data.getlist("gender_identities", [])],
        "identity_ethic": [get_id_or_create(EthicIdentities, ei) for ei in data.getlist("identity_ethic", [])],
        "identity_pronouns": [get_id_or_create(PronounsIdentities, pi) for pi in
                              data.getlist("pronouns_identities", [])],
        "disability": data.get("disability") == "true",
        "care_giver": data.get("care_giver") == "true",
        "veteran_status": data.get("veteran_status"),
        "how_connection_made": data.get("how_connection_made").lower(),
        "postal_code": data.get("postal_code"),
        "location": data.get("location"),
        "state": data.get("state"),
        "city": data.get("city"),
        "photo": files.get("photo"),
    }
    return profile_data


def extract_user_data(data):
    """
    Extracts and processes user-related data from the request data.

    Args:
        data (dict): The request data containing user-related fields.

    Returns:
        dict: A dictionary containing processed user data ready for creating or updating a user instance.

    The function processes the following user-related fields:
    - is_mentee: Determines if the user is a mentee.
    - is_mentor: Determines if the user is a mentor.
    - Other fields can be added as per the application's requirements.
    """

    return {
        "is_mentee": bool(data.get("is_mentee", "")),
        "is_mentor": bool(data.get("is_mentor", "")),
    }


def extract_company_data(data):
    """
    Extracts and processes company-related data from the request data.

    Args:
        data (dict): The request data containing user-related fields.

    Returns:
        dict: A dictionary containing processed user data ready for creating or updating a user instance.

    The function processes the following user-related fields:
    - company_name: The name of the user's company.
    - company_url: The URL of the user's company.
    - Other fields can be added as per the application's requirements.
    """

    return {
        "company_name": data.get("company_name", ""),
        "company_url": data.get("company_url", ""),
        "company_id": data.get("company_id", ""),
    }


def extract_profile_data(data, files):
    """
    Extract and process profile-related data from the request.

    This function processes the incoming data and files related to the user's profile. It handles:
    - Extracting profile data fields from the request.
    - Processing URLs to ensure they are correctly formatted.
    - Splitting comma-separated strings into lists.
    - Handling file uploads for photos.
    - Converting string 'True'/'False' or presence of value to boolean.

    :param data: The request data from which to extract profile information.
    :param files: The request files which may contain the photo.
    :return: A dictionary containing processed profile-related data.
    """
    profile_data = {
        "linkedin": prepend_https_if_not_empty(data.get("linkedin", "")),
        "instagram": data.get("instagram", ""),
        "github": prepend_https_if_not_empty(data.get("github", "")),
        "twitter": data.get("twitter", ""),
        "youtube": prepend_https_if_not_empty(data.get("youtube", "")),
        "personal": prepend_https_if_not_empty(data.get("personal", "")),
        "identity_sexuality": data.get("identity_sexuality", "").split(","),
        "is_identity_sexuality_displayed": bool(
            data.get("is_identity_sexuality_displayed", "")
        ),
        "identity_gender": data.get("gender_identities", "").split(","),
        "is_identity_gender_displayed": bool(
            data.get("is_identity_gender_displayed", "")
        ),
        "identity_ethic": data.get("identity_ethic", "").split(","),
        "is_identity_ethic_displayed": bool(
            data.get("is_identity_ethic_displayed", "")
        ),
        "identity_pronouns": data.get("pronouns_identities", "").split(",")
        if data.get("pronouns_identities")
        else "",
        "disability": bool(data.get("disability", "")),
        "is_disability_displayed": bool(data.get("is_disability_displayed", "")),
        "care_giver": bool(data.get("care_giver", "")),
        "is_care_giver_displayed": bool(data.get("is_care_giver_displayed", "")),
        "veteran_status": data.get("veteran_status", ""),
        "is_veteran_status_displayed": bool(
            data.get("is_veteran_status_displayed", "")
        ),
        "how_connection_made": data.get("how_connection_made", "").lower(),
        "is_pronouns_displayed": bool(data.get("is_pronouns_displayed", "")),
        "marketing_monthly_newsletter": bool(
            data.get("marketing_monthly_newsletter", "")
        ),
        "marketing_events": bool(data.get("marketing_events", "")),
        "marketing_identity_based_programing": bool(
            data.get("marketing_identity_based_programing", "")
        ),
        "marketing_jobs": bool(data.get("marketing_jobs", "")),
        "marketing_org_updates": bool(data.get("marketing_org_updates", "")),
        "postal_code": data.get("postal_code", ""),
        "tbc_program_interest": data.get("tbc_program_interest", "").split(",")
        if data.get("tbc_program_interest", "")
        else None,
        "photo": files["photo"] if "photo" in files else None,
    }

    return profile_data


def extract_profile_data_id(data, files):
    """
    Extract and process profile-related IDs data from the request.

    This function processes the incoming data and files related to the user's profile. It handles:
    - Extracting profile data fields from the request.
    - Processing URLs to ensure they are correctly formatted.
    - Splitting comma-separated strings into lists.
    - Handling file uploads for photos.
    - Converting string 'True'/'False' or presence of value to boolean.

    :param data: The request data from which to extract profile information.
    :param files: The request files which may contain the photo.
    :return: A dictionary containing processed profile-related data.
    """
    profile_data = {
        "linkedin": prepend_https_if_not_empty(data.get("linkedin", "")),
        "instagram": data.get("instagram", ""),
        "github": prepend_https_if_not_empty(data.get("github", "")),
        "twitter": data.get("twitter", ""),
        "youtube": prepend_https_if_not_empty(data.get("youtube", "")),
        "personal": prepend_https_if_not_empty(data.get("personal", "")),
        "identity_sexuality": [get_id_or_create(SexualIdentities, si) for si in data.getlist("identity_sexuality", [])],
        "identity_gender": [get_id_or_create(GenderIdentities, gi) for gi in data.getlist("gender_identities", [])],
        "identity_ethic": [get_id_or_create(EthicIdentities, ei) for ei in data.getlist("identity_ethic", [])],
        "identity_pronouns": [get_id_or_create(PronounsIdentities, pi) for pi in
                              data.getlist("pronouns_identities", [])],
        "disability": bool(data.get("disability", "")),
        "is_disability_displayed": bool(data.get("is_disability_displayed", "")),
        "care_giver": bool(data.get("care_giver", "")),
        "is_care_giver_displayed": bool(data.get("is_care_giver_displayed", "")),
        "veteran_status": data.get("veteran_status", ""),
        "is_veteran_status_displayed": bool(
            data.get("is_veteran_status_displayed", "")
        ),
        "how_connection_made": data.get("how_connection_made", "").lower(),
        "is_pronouns_displayed": bool(data.get("is_pronouns_displayed", "")),
        "marketing_monthly_newsletter": bool(
            data.get("marketing_monthly_newsletter", "")
        ),
        "marketing_events": bool(data.get("marketing_events", "")),
        "marketing_identity_based_programing": bool(
            data.get("marketing_identity_based_programing", "")
        ),
        "marketing_jobs": bool(data.get("marketing_jobs", "")),
        "marketing_org_updates": bool(data.get("marketing_org_updates", "")),
        "postal_code": data.get("postal_code", ""),
        "tbc_program_interest": data.get("tbc_program_interest", "").split(",")
        if data.get("tbc_program_interest", "")
        else None,
        "photo": files["photo"] if "photo" in files else None,
    }

    return profile_data


def extract_talent_data(data, files):
    """
    Extracts and processes talent-related data from the request.

    The function processes incoming data to structure it according to the MemberProfile model's needs.
    It handles extracting and converting data, ensuring that multi-value fields are appropriately split and
    that file fields are handled correctly.

    Args:
    data (dict): The request data containing talent-related information.
    files (dict): The uploaded files in the request.

    Returns:
    dict: A dictionary containing processed talent data ready to be used in a MemberProfile serializer or model.
    """

    talent_data = {
        "tech_journey": data.get("years_of_experience", []),
        "is_talent_status": data.get("talent_status", False),
        "company_types": data.get("company_types", "").split(",")
        if data.get("company_types")
        else [],
        "department": data.get("job_department", "").split(",")
        if data.get("job_department")
        else [],
        "role": data.get("job_roles", "").split(",") if data.get("job_roles") else [],
        "skills": data.get("job_skills", "").split(",")
        if data.get("job_skills")
        else [],
        "max_compensation": data.get("max_compensation", []),
        "min_compensation": data.get("min_compensation", []),
        "resume": files.get("resume") if "resume" in files else None,
    }

    # Ensuring that the list fields containing IDs are actually lists of integers
    for field in ["max_compensation", "min_compensation"]:
        if isinstance(talent_data[field], list):
            talent_data[field] = [int(i) for i in talent_data[field] if i.isdigit()]

    # Convert boolean fields from string to actual boolean values
    talent_data["is_talent_status"] = bool(talent_data["is_talent_status"])

    # Clean up list fields to ensure there are no empty strings
    for list_field in ["company_types", "department", "role", "skills"]:
        talent_data[list_field] = [
            item for item in talent_data[list_field] if item.strip()
        ]

    return talent_data


def process_company_types(company_types):
    """
    Process the given list of company types. It ensures that each company type is valid
    and corresponds to a CompanyType instance in the database. If a company type does not
    exist, it will be created.

    Args:
    company_types (list): A list of company type names or IDs.

    Returns:
    QuerySet: A QuerySet of CompanyType instances that are associated with the provided company types.

    Raises:
    ValueError: If a company type is invalid or cannot be processed.
    """
    company_type_instances = []
    for company_type in company_types:
        # Skip empty strings or None values
        if not company_type:
            continue

        try:
            # Attempt to get the CompanyType by name or ID
            if isinstance(company_type, int):
                # If company_type is an int, we assume it's an ID
                company_type_instance, created = CompanyTypes.objects.get_or_create(
                    id=company_type
                )
            else:
                # If company_type is a string, we assume it's the name of the company type
                company_type_instance, created = CompanyTypes.objects.get_or_create(
                    name=company_type
                )

            company_type_instances.append(company_type_instance)
        except CompanyTypes.MultipleObjectsReturned:
            # This block handles the case where get_or_create returns multiple objects
            raise ValueError(f"Multiple company types found for: {company_type}")
        except Exception as e:
            # Handle other exceptions such as database errors
            raise ValueError(f"Error processing company type {company_type}: {str(e)}")

    return company_type_instances


def process_roles(role_identifiers):
    """
    Process and validate role identifiers before setting them in the MemberProfile.

    This function takes a list of role identifiers, which can be names or IDs, and returns the corresponding
    Role instances after validating their existence in the database. If a role does not exist, it's created.

    Args:
    role_identifiers (list): A list of role names or IDs.

    Returns:
    QuerySet or list: A QuerySet or list of Role model instances to be associated with the MemberProfile.

    Raises:
    ValueError: If any of the identifiers is invalid or if the role cannot be found or created.
    """
    if not isinstance(role_identifiers, list) or not all(role_identifiers):
        raise ValueError("Role identifiers must be a non-empty list.")

    roles_to_set = []
    for identifier in role_identifiers:
        # Check and remove 'Add "' prefix and trailing '"' if present
        if identifier.startswith('Add "') and identifier.endswith('"'):
            identifier = identifier[5:-1].strip()

        try:
            # If identifier is a role ID
            if isinstance(identifier, int):
                role = Roles.objects.get(id=identifier)
            # If identifier is a role name
            elif isinstance(identifier, str):
                role, created = Roles.objects.get_or_create(name=identifier)

                if created:
                    print(f"Created new role: {identifier.name}")
            else:
                raise ValueError(f"Invalid role identifier: {identifier}")

            roles_to_set.append(role)
        except Roles.DoesNotExist:
            raise ValueError(f"Role not found for identifier: {identifier}")
        except Roles.MultipleObjectsReturned:
            raise ValueError(f"Multiple roles returned for identifier: {identifier}")
        except Exception as e:
            # Log the exception for debugging
            print(f"Error in process_roles: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise

    return roles_to_set


def process_departments(department_names):
    """
    Process and validate department names before setting them in the MemberProfile.

    This function ensures that all department names provided are valid and correspond to existing
    Department instances in the database. If a department does not exist, it's created.

    Args:
    department_names (list of str): A list of department names.

    Returns:
    QuerySet: A QuerySet of Department instances to be associated with the MemberProfile.

    Raises:
    ValueError: If any of the department names are invalid (e.g., empty strings or not matching any predefined departments).
    """
    if not department_names or not isinstance(department_names, list):
        raise ValueError("Department names should be a non-empty list.")

    department_set = []
    for name in department_names:
        if not name:
            # Handle empty string or None
            raise ValueError("Department name cannot be empty or None.")

        # Check and remove 'Add "' prefix and trailing '"' if present
        if name.startswith('Add "') and name.endswith('"'):
            name = name[5:-1].strip()

        try:
            # Check if department exists, if not, create it
            k = name.strip()
            department, created = Department.objects.get_or_create(name=k)
            department_set.append(department)
            if created:
                print(f"Created new department: {department.name}")
        except Exception as e:
            # Log the exception and skip this department
            print(f"Failed to create or retrieve department '{name.strip()}': {e}")
            continue

    # Return a QuerySet or a list of Department instances
    return department_set


def process_skills(skill_list):
    """
    Process and validate skills before setting them in the MemberProfile.

    This function takes a list of skill names or identifiers, ensures that these skills
    are present in the database (creating them if necessary), and returns a queryset
    or list of Skill model instances.

    Args:
    skill_list (list): A list of skill names or identifiers.

    Returns:
    QuerySet: A QuerySet of Skill instances to be associated with the MemberProfile.

    Raises:
    ValueError: If any of the skills are invalid or cannot be processed.
    """
    skill_instances = []

    for skill_name in skill_list:
        # Validate or process skill_name here (e.g., check if it's a non-empty string)
        if not skill_name or not isinstance(skill_name, str):
            raise ValueError(f"Invalid skill name: {skill_name}")

        # Check and remove 'Add "' prefix and trailing '"' if present
        if skill_name.startswith('Add "') and skill_name.endswith('"'):
            skill_name = skill_name[5:-1].strip()

        # Try to get the skill by name, or create it if it doesn't exist
        try:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            if created:
                print(f"Created new department: {skill.name}")
            skill_instances.append(skill)
        # Optionally, handle the case where the skill creation failed (if get_or_create does not meet your needs)
        except Exception as e:
            raise ValueError(
                f"Failed to create or retrieve skill with name: {skill_name}. Error: {e}"
            )
    return skill_instances


def process_compensation(compensation_data, default_value=None):
    """
    Process and validate compensation data before setting it in the MemberProfile.

    Args:
        compensation_data (list): A list containing compensation range IDs or values.
        default_value (SalaryRange or None): The default SalaryRange to return if compensation_data is empty.

    Returns:
        SalaryRange or None: The SalaryRange model instance to be associated with the MemberProfile, or the default value.

    Raises:
        ValidationError: If the compensation data is not valid or does not meet the business requirements.
    """
    if not compensation_data:
        # If compensation_data is empty or None, return the default_value
        return default_value

    compensation_to_set = []
    for comp_id in compensation_data:
        try:
            # Assuming comp_id is the ID of the SalaryRange, try to fetch the SalaryRange instance
            salary_range = SalaryRange.objects.get(id=comp_id)
            compensation_to_set.append(salary_range)
        except SalaryRange.DoesNotExist:
            # Handle the case where the SalaryRange does not exist for the given id
            raise ValidationError(f"Salary range with id {comp_id} does not exist.")
        except SalaryRange.MultipleObjectsReturned:
            # Handle the case where multiple SalaryRanges are returned for the given id
            raise ValidationError(f"Multiple salary ranges found for id {comp_id}.")
        except ValueError:
            # Handle the case where comp_id is not a valid integer (if ids are integers)
            raise ValidationError(f"Invalid id: {comp_id}. Id must be an integer.")

    return compensation_to_set[0] if compensation_to_set else default_value


def get_current_company_data(user):
    """
    Retrieve data of the company where the given user is currently employed.

    This function fetches the company associated with the given user as a current employee. It extracts
    and returns relevant company data, including the company's ID, name, logo, size, and industries.

    Args:
        user (CustomUser): The user whose current company data is to be retrieved.

    Returns:
        dict: A dictionary containing the company's ID, name, logo URL, size, and list of industries,
              if the company is found. For example:
              {
                  "id": 1,
                  "company_name": "Example Corp",
                  "logo": "/media/logo_pics/default-logo.jpeg",
                  "company_size": "501-1000",
                  "industries": ["Tech", "Media"]
              }
        None: If the user is not currently associated with any company or the company does not exist.

    Raises:
        CompanyProfile.DoesNotExist: If no CompanyProfile is associated with the user as a current employee.
    """
    try:
        company = CompanyProfile.objects.get(current_employees=user)
        return {
            "id": company.id,
            "company_name": company.company_name,
            "logo": company.logo.url,
            "company_size": company.company_size,
            "industries": [industry.name for industry in company.industries.all()],
        }
    except CompanyProfile.DoesNotExist:
        return None
