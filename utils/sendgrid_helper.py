import json
import logging
import os

import requests

# Get an instance of a logger
logger = logging.getLogger(__name__)

base_url = "https://api.convertkit.com/v3/"

headers = {
    "Content-Type": "application/json",
    "charset": "utf-8"
}


# this adds people to the newsletter sequences
def add_user_to_newsletter(details):
    # Set the data for the request
    welcome_sequences_id = os.getenv("CONVERTKIT_WELCOME_SEQUENCE_ID")

    url = f'{base_url}sequences/{welcome_sequences_id}/subscribe'
    data = {
        "api_key": os.getenv("CONVERTKIT_API_KEY"),
        "first_name": details["first_name"],
        "email": details["email"],
    }
    try:
        # Make the POST request to the ConvertKit API
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check the response status code
        if response.status_code <= 200:
            print("User added to form successfully.")
        else:
            print(f"Error adding user to form: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error adding user to form: {e}")


def add_user_to_portal_form(details):
    # Set the data for the request

    tbc_portal_form = os.getenv("CONVERTKIT_PORTAL_FORM_ID")
    url = f'{base_url}forms/{tbc_portal_form}/subscribe'
    data = {
        "api_key": os.getenv("CONVERTKIT_API_KEY"),
        "first_name": details["first_name"],
        "email": details["email"],
    }
    try:
        # Make the POST request to the ConvertKit API
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_json = response.json()
        user_id = response_json.get("subscription").get("id")
        tags_url = f'{base_url}tags/{os.getenv("CONVERTKIT_NEW_USER_TAG_ID")}/subscribe'
        tag_data = {
            "api_key": os.getenv("CONVERTKIT_API_KEY"),
            "email": details["email"]
        }

        # Check the response status code
        if response.status_code <= 200:
            print("User added to tbc portal form successfully.")
            try:
                tag_response = requests.post(tags_url, headers=headers, data=json.dumps(data))
                if tag_response.status_code <= 200:
                    print("User successfully added tagged with New User tag.")
            except requests.exceptions.RequestException as e:
                print(f"Error adding user to tbc portal form: {e}")
        else:
            print(f"Error adding user to tbc portal form: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error adding user to tbc portal form: {e}")


def remove_user_from_convertkit(email):
    """
    Remove a user from ConvertKit.

    Args:
        email (str): The email of the user to be removed.

    Returns:
        bool: True if the user was successfully removed, False otherwise.
    """
    api_secret = os.getenv("CONVERTKIT_API_SECRET_KEY")
    url = f'{base_url}unsubscribe'

    trimmed_email = email.strip()

    data = {
        "api_secret": api_secret,
        "email": trimmed_email
    }

    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            logger.info(f"User {email} successfully removed from ConvertKit.")
            return True
        else:
            logger.error(f"Error removing user {email} from ConvertKit: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error removing user {email} from ConvertKit: {str(e)}")
        return False
