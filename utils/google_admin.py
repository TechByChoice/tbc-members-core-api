import json
import os

import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build

from api.settings import STATIC_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME

# Constants
SCOPES = ["https://www.googleapis.com/auth/admin.directory.user"]
SERVICE_ACCOUNT_FILE = f"{STATIC_URL}tbc-member-platform.json"
SERVICE_ACCOUNT_FILE_KEY = "static/tbc-member-platform.json"


def get_s3_file_content(bucket_name, file_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    return content


def get_admin_sdk_service():
    file_content = get_s3_file_content(os.getenv("AWS_STORAGE_BUCKET_NAME"), SERVICE_ACCOUNT_FILE_KEY)
    service_account_info = json.loads(file_content)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )

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
