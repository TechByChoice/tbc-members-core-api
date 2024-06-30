from apps.company.models import CompanyProfile


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
    company_id = company_data.get("company_id")
    company_name = company_data.get("company_name")
    company_url = company_data.get("company_url")
    company_logo = company_data.get("company_logo")

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
        if company_name and company_url:
            company_profile = CompanyProfile.objects.create(
                unclaimed_account_creator=user,
                is_unclaimed_account=True,
                company_name=company_name,
                # logo=company_logo,
                company_url=company_url,
            )
            company_profile.current_employees.add(user)
            return company_profile
        else:
            return False
