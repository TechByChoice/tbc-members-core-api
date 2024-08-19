import json
import logging
import os

import requests

from utils.urls_utils import extract_domain

C_TOKEN = os.getenv("C_TOKEN")
DEV_LOGO_KEY = os.getenv("DEV_LOGO_KEY")

logger = logging.getLogger(__name__)


def map_employee_count_to_company_size(employee_count):
    if employee_count is None:
        return "unknown"

    employee_count = int(employee_count)

    if 1 <= employee_count <= 20:
        return "1 - 20"
    elif 21 <= employee_count <= 100:
        return "21 - 100"
    elif 101 <= employee_count <= 500:
        return "101 - 500"
    elif 501 <= employee_count <= 1000:
        return "501 - 1000"
    elif 1001 <= employee_count <= 5000:
        return "1001 - 5000"
    elif employee_count >= 5001:
        return "5001"
    else:
        return "unknown"


def pull_company_info(company_obj):
    # Pull and save external company data.
    company_name = company_obj.company_name
    company_id = company_obj.coresignal_id
    company_url = company_obj.company_url

    if company_name is None:
        logging.error("Missing company_name. Ending now")
        return False
    if company_obj.coresignal_id:
        try:
            url = f"https://api.coresignal.com/cdapi/v1/linkedin/company/collect/{company_id}"
            # url = f"https://api.coresignal.com/cdapi/v1/linkedin/company/search/filter"
            # url = f"https://api.coresignal.com/enrichment/companies?website={company_name}&lookalikes=false"
            response = requests.get(url, data=json.dumps({"name": company_name}), headers={'Authorization': f'Bearer {C_TOKEN}'})
            response.raise_for_status()
            response_data = response.json()
            return save_company_info(company_obj, response_data)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Error pulling company data from 3rd party: {http_err}")
            return False
    else:
        try:
            # url = f"https://api.coresignal.com/cdapi/v1/linkedin/company/collect/{company_id}"
            # url = f"https://api.coresignal.com/cdapi/v1/linkedin/company/search/filter"
            url = f"https://api.coresignal.com/enrichment/companies?website={company_name}&lookalikes=false"
            response = requests.get(url, data=json.dumps({"name": company_name}), headers={'Authorization': f'Bearer {C_TOKEN}'})
            response.raise_for_status()
            response_data = response.json()
            return save_company_info(company_obj, response_data.get('data'))
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Error pulling company data from 3rd party: {http_err}")
            return False


def save_company_info(company_obj, new_company_info):
    print(new_company_info)
    try:
        company_obj.company_url = new_company_info.get('website')
        company_obj.mission = new_company_info.get('description')
        company_obj.linkedin_url = new_company_info.get('linkedin_url')
        company_obj.location = new_company_info.get('location')
        company_obj.company_size = map_employee_count_to_company_size(new_company_info.get('employees_count'))
        company_obj.industry = new_company_info.get('industry')
        company_obj.logo_url = new_company_info.get('logo_url')
        company_obj.coresignal_id = new_company_info.get('id')
        company_domain = extract_domain(new_company_info.get('website'))
        logo_url = f"https://img.logo.dev/{company_domain}?token={DEV_LOGO_KEY}"

        # Handle logo
        company_obj.logo = logo_url

        company_obj.save()
        logger.info(f"Successfully updated company info for {company_obj.company_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving company info: {str(e)}")
        return False
