import os
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from django.core.exceptions import ObjectDoesNotExist

from apps.core.models import CustomUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync Slack users to ConvertKit with a specific tag and update TBC user status'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slack_token = os.environ.get('SLACK_API_TOKEN')
        self.convertkit_api_key = os.environ.get('CONVERTKIT_API_KEY')
        self.convertkit_tag_id = "3378251"

        if not self.slack_token:
            raise ValueError('SLACK_API_TOKEN not found in environment variables')
        if not self.convertkit_api_key:
            raise ValueError('CONVERTKIT_API_KEY not found in environment variables')

        self.slack_client = WebClient(token=self.slack_token)
        self.convertkit_base_url = 'https://api.convertkit.com/v3'

    def handle(self, *args, **options):
        logger.info("Starting Slack to ConvertKit sync process")
        slack_users = self.get_all_slack_users()
        self.sync_users_to_convertkit(slack_users)
        logger.info("Completed Slack to ConvertKit sync process")

    def get_all_slack_users(self):
        users = []
        cursor = None
        while True:
            try:
                response = self.slack_client.users_list(limit=200, cursor=cursor)
                users.extend(response['members'])
                cursor = response['response_metadata']['next_cursor']
                if not cursor:
                    break
                time.sleep(1)  # Rate limiting
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retry_after = int(e.response.headers.get('Retry-After', 30))
                    logger.warning(f"Rate limited by Slack API. Waiting for {retry_after} seconds")
                    time.sleep(retry_after)
                else:
                    logger.error(f"Error fetching Slack users: {e}")
                    break

        logger.info(f"Retrieved {len(users)} users from Slack")
        return users

    def sync_users_to_convertkit(self, users):
        for user in users:
            if not user['is_bot'] and not user['deleted'] and 'email' in user['profile']:
                email = user['profile']['email']
                name = user['real_name']

                try:
                    tbc_user = CustomUser.objects.get(email=email)
                    tbc_user.is_slack_active = True
                    tbc_user.save()
                    logger.info(f"Updated is_slack_active to True for user: {email}")
                except ObjectDoesNotExist:
                    logger.warning(f"User with email {email} not found in TBC database")

                self.add_user_to_convertkit(email, name)
                time.sleep(1)  # Rate limiting for ConvertKit API

    def add_user_to_convertkit(self, email, name):
        url = f"{self.convertkit_base_url}/tags/{self.convertkit_tag_id}/subscribe"
        data = {
            'api_key': self.convertkit_api_key,
            'email': email,
            'first_name': name
        }

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Successfully added {email} to ConvertKit with tag")
        except requests.RequestException as e:
            logger.error(f"Failed to add {email} to ConvertKit: {str(e)}")


if __name__ == '__main__':
    from django.core.management import execute_from_command_line

    execute_from_command_line(['manage.py', 'sync_slack_to_convertkit'])