import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

from api.settings import STATIC_URL

# Constants
SCOPES = ["https://www.googleapis.com/auth/admin.directory.user"]
SERVICE_ACCOUNT_FILE = STATIC_URL + 'tbc-member-platform.json'


def get_admin_sdk_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    # Assuming your Django project is properly set up with the domain admin email
    delegated_credentials = credentials.with_subject(os.environ["GOOGLE_ADMIN_EMAIL"])
    try:
        service = build("admin", "directory_v1", credentials=delegated_credentials)
        return service
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_user(user_data):
    service = get_admin_sdk_service()
    try:
        user = service.users().insert(body=user_data).execute()
        return user
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
