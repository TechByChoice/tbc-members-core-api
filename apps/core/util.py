from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from utils.errors import CustomException
from .models import UserProfile, SexualIdentities, GenderIdentities, EthicIdentities, PronounsIdentities
from .serializers import UpdateCustomUserSerializer
from ..company.models import CompanyTypes, Department, Skill, SalaryRange, Roles, CompanyProfile
from ..talent.models import TalentProfile

User = get_user_model()


def create_or_update_user(current_user, user_data):
    """
    Create or update a user instance based on the provided user_data.

    :param current_user: The user instance to update.
    :param user_data: A dictionary containing the data for the user.
    :return: The created or updated user instance.
    """
    try:
        # Assuming you're partially updating an existing user
        user_serializer = UpdateCustomUserSerializer(instance=current_user, data=user_data, partial=True)

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


def create_or_update_talent_profile(user, talent_data):
    """
    Create or update the TalentProfile for a given user.

    Args:
    user (User model instance): The user for whom the TalentProfile needs to be created or updated.
    talent_data (dict): A dictionary containing all the necessary data to create or update a TalentProfile.

    Returns:
    TalentProfile: The created or updated TalentProfile instance.

    Raises:
    ValidationError: If the provided data is not valid to create or update a TalentProfile.
    """
    try:
        # Check if the user already has a TalentProfile
        talent_profile = TalentProfile.objects.get(user=user)

        # Update or set fields in talent_profile from talent_data
        talent_profile.tech_journey = talent_data.get('tech_journey', talent_profile.tech_journey)
        talent_profile.is_talent_status = talent_data.get('talent_status', talent_profile.is_talent_status)

        # Handle many-to-many fields like company_types, roles, departments, skills, etc.
        # TODO: Testing Fix | we can use the process_identity_field() to simplify the code here
        talent_profile.company_types.set(process_company_types(talent_data.get('company_types', [])))
        talent_profile.role.set(process_roles(talent_data.get('role', [])))
        # Department is one that's messed up on prod so it's one I'm checking first
        talent_profile.department.set(process_departments(talent_data.get('department', [])))
        talent_profile.skills.set(process_skills(talent_data.get('skills', [])))

        # Handle compensation ranges
        talent_profile.min_compensation = process_compensation(talent_data.get('min_compensation', []))
        talent_profile.max_compensation = process_compensation(talent_data.get('max_compensation', []))


        # Handle file fields like resume
        if 'resume' in talent_data and talent_data['resume'] is not None:
            talent_profile.resume = talent_data['resume']

        # Save the updated profile
        talent_profile.save()
        return talent_profile

    except Exception as e:
        # Log the exception for debugging
        print(f"Error in create_or_update_talent_profile: {str(e)}")
        # Re-raise the exception to be handled by the caller
        raise


def create_or_update_user_profile(user, profile_data):
    """
    Create or update a user profile.

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
        user_profile, created = UserProfile.objects.get_or_create(user=user, defaults=profile_data)

        # Process and set many-to-many fields
        if 'identity_sexuality' in profile_data and not profile_data['identity_sexuality'] == ['']:
            sexuality_instances = process_identity_field(profile_data['identity_sexuality'], SexualIdentities)
            user_profile.identity_sexuality.set(sexuality_instances)

        if 'identity_gender' in profile_data and not profile_data['identity_gender'] == ['']:
            gender_instances = process_identity_field(profile_data['identity_gender'], GenderIdentities)
            user_profile.identity_gender.set(gender_instances)

        if 'identity_ethic' in profile_data and not profile_data['identity_ethic'] == ['']:
            ethic_instances = process_identity_field(profile_data['identity_ethic'], EthicIdentities)
            user_profile.identity_ethic.set(ethic_instances)

        if 'identity_pronouns' in profile_data and not profile_data['identity_pronouns'] == ['']:
            pronouns_instances = process_identity_field(profile_data['identity_pronouns'], PronounsIdentities)
            user_profile.identity_pronouns.set(pronouns_instances)

        # For fields that are not many-to-many relationships, update them directly
        # TODO: Testing Fix | I'm looping through all the items when I should
        #  only loop through the ones for this grouping
        for field, value in profile_data.items():
            if field not in ['identity_sexuality', 'identity_gender', 'identity_ethic', 'identity_pronouns']:
                setattr(user_profile, field, value)

        user_profile.save()
        return user_profile
    except Exception as e:
        # Log the exception and raise a custom exception for the caller to handle
        print(f"Error in create_or_update_user_profile: {str(e)}")
        raise CustomException(f"Failed to create or update UserProfile: {str(e)}")


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
            raise ValueError(f"Failed to create or retrieve name with name: {identity_name}")

        identity_instances.append(identity)

    return identity_instances


def create_or_update_company_connection(user, company_data):
    """
    Create or update a company connection for a user.

    This function checks if the company is already in the database. If so, it adds the user
    to the company's current employees. If the company is not in the database, it creates a
    new company with the user as the unclaimed_account_creator and adds them to current_employees.
    It also moves the user from current to past employees in their previous company, if applicable.

    Parameters:
    - user (CustomUser): The user to add to the company.
    - company_data (dict): A dictionary containing company_id, company_name, company_url, and company_logo.

    Returns:
    - CompanyProfile: The company profile object that the user was added to.
    """
    company_id = company_data.get('company_id')
    company_name = company_data.get('company_name')
    company_url = company_data.get('company_url')
    company_logo = company_data.get('company_logo')

    # Check if the user is currently associated with a different company
    previous_company = CompanyProfile.objects.filter(current_employees=user).first()
    if previous_company:
        previous_company.current_employees.remove(user)
        previous_company.past_employees.add(user)

    if company_id:
        # The company already exists, just add the user to current_employees
        company_profile = CompanyProfile.objects.get(id=company_id)
        company_profile.current_employees.add(user)
    else:
        # The company doesn't exist, create a new one and set user as unclaimed_account_creator and in current_employees
        if company_name and company_url and company_logo:
            company_profile = CompanyProfile.objects.create(
                unclaimed_account_creator=user,
                is_unclaimed_account=True,
                company_name=company_name,
                logo=company_logo,
                company_url=company_url
            )
            company_profile.current_employees.add(user)
            return company_profile
        else:
            return False





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
        'is_mentee': bool(data.get('is_mentee', '')),
        'is_mentor': bool(data.get('is_mentor', '')),
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
        'company_name': data.get('company_name', ''),
        'company_url': data.get('company_url', ''),
        'company_id': data.get('company_id', ''),
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
        'linkedin': prepend_https_if_not_empty(data.get('linkedin', '')),
        'instagram': data.get('instagram', ''),
        'github': prepend_https_if_not_empty(data.get('github', '')),
        'twitter': data.get('twitter', ''),
        'youtube': prepend_https_if_not_empty(data.get('youtube', '')),
        'personal': prepend_https_if_not_empty(data.get('personal', '')),
        'identity_sexuality': data.get('identity_sexuality', '').split(','),
        'is_identity_sexuality_displayed': bool(data.get('is_identity_sexuality_displayed', '')),
        'identity_gender': data.get('gender_identities', '').split(','),
        'is_identity_gender_displayed': bool(data.get('is_identity_gender_displayed', '')),
        'identity_ethic': data.get('identity_ethic', '').split(','),
        'is_identity_ethic_displayed': bool(data.get('is_identity_ethic_displayed', '')),
        'identity_pronouns': data.get('pronouns_identities', '').split(',') if data.get(
            'pronouns_identities') else None,
        'disability': bool(data.get('disability', '')),
        'is_disability_displayed': bool(data.get('is_disability_displayed', '')),
        'care_giver': bool(data.get('care_giver', '')),
        'is_care_giver_displayed': bool(data.get('is_care_giver_displayed', '')),
        'veteran_status': data.get('veteran_status', ''),
        'is_veteran_status_displayed': bool(data.get('is_veteran_status_displayed', '')),
        'how_connection_made': data.get('how_connection_made', '').lower(),
        'is_pronouns_displayed': bool(data.get('is_pronouns_displayed', '')),
        'marketing_monthly_newsletter': bool(data.get('marketing_monthly_newsletter', '')),
        'marketing_events': bool(data.get('marketing_events', '')),
        'marketing_identity_based_programing': bool(data.get('marketing_identity_based_programing', '')),
        'marketing_jobs': bool(data.get('marketing_jobs', '')),
        'marketing_org_updates': bool(data.get('marketing_org_updates', '')),
        'postal_code': data.get('postal_code', ''),
        'tbc_program_interest': data.get('tbc_program_interest', ''),
        'photo': files['photo'] if 'photo' in files else None,
    }

    # Process name fields to ensure they are lists or None if empty
    # profile_data['identity_sexuality'] = process_identity_field(profile_data['identity_sexuality'], SexualIdentities)
    # profile_data['identity_gender'] = process_identity_field(profile_data['identity_gender'], GenderIdentities)
    # profile_data['identity_ethic'] = process_identity_field(profile_data['identity_ethic'], EthicIdentities)
    # profile_data['identity_pronouns'] = process_identity_field(profile_data['identity_pronouns'], PronounsIdentities)

    return profile_data


def extract_talent_data(data, files):
    """
    Extracts and processes talent-related data from the request.

    The function processes incoming data to structure it according to the TalentProfile model's needs.
    It handles extracting and converting data, ensuring that multi-value fields are appropriately split and
    that file fields are handled correctly.

    Args:
    data (dict): The request data containing talent-related information.
    files (dict): The uploaded files in the request.

    Returns:
    dict: A dictionary containing processed talent data ready to be used in a TalentProfile serializer or model.
    """

    talent_data = {
        'tech_journey': data.get('years_of_experience', []),
        'is_talent_status': data.get('talent_status', False),
        'company_types': data.get('company_types', '').split(',') if data.get('company_types') else [],
        'department': data.get('job_department', '').split(',') if data.get('job_department') else [],
        'role': data.get('job_roles', '').split(',') if data.get('job_roles') else [],
        'skills': data.get('job_skills', '').split(',') if data.get('job_skills') else [],
        'max_compensation': data.get('max_compensation', []),
        'min_compensation': data.get('min_compensation', []),
        'resume': files.get('resume') if 'resume' in files else None
    }

    # Ensuring that the list fields containing IDs are actually lists of integers
    for field in ['max_compensation', 'min_compensation']:
        if isinstance(talent_data[field], list):
            talent_data[field] = [int(i) for i in talent_data[field] if i.isdigit()]

    # Convert boolean fields from string to actual boolean values
    talent_data['is_talent_status'] = bool(talent_data['is_talent_status'])

    # Clean up list fields to ensure there are no empty strings
    for list_field in ['company_types', 'department', 'role', 'skills']:
        talent_data[list_field] = [item for item in talent_data[list_field] if item.strip()]

    return talent_data


def prepend_https_if_not_empty(url):
    """
    Prepend 'https://' to the URL if it's not empty and doesn't already start with 'http'.

    :param url: The URL string to process.
    :return: The processed URL string with 'https://' prepended if applicable.
    """
    if url and not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url


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
            raise ValueError(f"Invalid name name: {identity_name}")

        # Try to get the name by name, or create it if it doesn't exist
        identity, created = model.objects.get_or_create(name=identity_name.strip())

        # Optionally, handle the case where the name creation failed (if get_or_create does not meet your needs)
        if not identity:
            raise ValueError(f"Failed to create or retrieve name with name: {identity_name}")

        identity_instances.append(identity)

    return identity_instances


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
                company_type_instance, created = CompanyTypes.objects.get_or_create(id=company_type)
            else:
                # If company_type is a string, we assume it's the name of the company type
                company_type_instance, created = CompanyTypes.objects.get_or_create(name=company_type)

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
    Process and validate role identifiers before setting them in the TalentProfile.

    This function takes a list of role identifiers, which can be names or IDs, and returns the corresponding
    Role instances after validating their existence in the database. If a role does not exist, it's created.

    Args:
    role_identifiers (list): A list of role names or IDs.

    Returns:
    QuerySet or list: A QuerySet or list of Role model instances to be associated with the TalentProfile.

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
    Process and validate department names before setting them in the TalentProfile.

    This function ensures that all department names provided are valid and correspond to existing
    Department instances in the database. If a department does not exist, it's created.

    Args:
    department_names (list of str): A list of department names.

    Returns:
    QuerySet: A QuerySet of Department instances to be associated with the TalentProfile.

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
    Process and validate skills before setting them in the TalentProfile.

    This function takes a list of skill names or identifiers, ensures that these skills
    are present in the database (creating them if necessary), and returns a queryset
    or list of Skill model instances.

    Args:
    skill_list (list): A list of skill names or identifiers.

    Returns:
    QuerySet: A QuerySet of Skill instances to be associated with the TalentProfile.

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
            skill, created = Skill.objects.get_or_create(name=skill_name.strip())
            if created:
                print(f"Created new department: {skill.name}")
            skill_instances.append(skill)
        # Optionally, handle the case where the skill creation failed (if get_or_create does not meet your needs)
        except Exception as e:
            raise ValueError(f"Failed to create or retrieve skill with name: {skill_name}. Error: {e}")
    return skill_instances


def process_compensation(compensation_data, default_value=None):
    """
    Process and validate compensation data before setting it in the TalentProfile.

    Args:
        compensation_data (list): A list containing compensation range IDs or values.
        default_value (SalaryRange or None): The default SalaryRange to return if compensation_data is empty.

    Returns:
        SalaryRange or None: The SalaryRange model instance to be associated with the TalentProfile, or the default value.

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
            raise ValidationError(f'Salary range with id {comp_id} does not exist.')
        except SalaryRange.MultipleObjectsReturned:
            # Handle the case where multiple SalaryRanges are returned for the given id
            raise ValidationError(f'Multiple salary ranges found for id {comp_id}.')
        except ValueError:
            # Handle the case where comp_id is not a valid integer (if ids are integers)
            raise ValidationError(f'Invalid id: {comp_id}. Id must be an integer.')

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
            "industries": [industry.name for industry in company.industries.all()]
        }
    except CompanyProfile.DoesNotExist:
        return None