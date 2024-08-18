import os
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from apps.core.models import CustomUser


class Command(BaseCommand):
    help = 'Sync active members with Slack users and check for pending invitations'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slack_token = os.environ.get('SLACK_API_TOKEN')
        self.slack_admin_token = os.environ.get('SLACK_API_ADMIN_TOKEN')
        if not self.slack_token:
            raise ValueError('SLACK_API_TOKEN not found in environment variables')
        if not self.slack_admin_token:
            raise ValueError('SLACK_API_ADMIN_TOKEN not found in environment variables')
        self.client = WebClient(token=self.slack_token)
        self.admin_client = WebClient(token=self.slack_admin_token)

    def handle(self, *args, **options):
        active_members = CustomUser.objects.filter(is_active=True, slack_user_id__isnull=True)
        self.sync_users(active_members)

    def sync_users(self, users):
        for user in users:
            self.sync_user(user)
            time.sleep(1)  # Wait for 1 second between API calls to avoid rate limiting

    def sync_user(self, user):
        try:
            # Look up user by email in Slack
            result = self.client.users_lookupByEmail(email=user.email)

            # User found in Slack
            slack_user = result['user']
            user.slack_id = slack_user['id']
            user.is_slack_active = not slack_user['deleted']
            user.is_slack_invite_sent = True
            user.is_slack_found_with_user_email = True
            self.stdout.write(self.style.SUCCESS(f"Updated Slack info for {user.email}"))

        except SlackApiError as e:
            if e.response['error'] == 'users_not_found':
                # User not found in Slack, check for pending invitation
                self.check_pending_invitation(user)
            elif e.response['error'] == 'user_deactivated':
                # User has been deactivated in Slack
                user.is_slack_active = False
                user.is_slack_invite_sent = True
                user.is_slack_found_with_user_email = True
                self.stdout.write(self.style.WARNING(f"User deactivated in Slack: {user.email}"))
            elif e.response['error'] == 'ratelimited':
                # Handle rate limiting
                retry_after = int(e.response.headers.get('Retry-After', 30))
                self.stdout.write(self.style.WARNING(f"Rate limited. Waiting for {retry_after} seconds"))
                time.sleep(retry_after)
                # Retry the sync for this user
                self.sync_user(user)
                return
            else:
                # Other API errors
                self.stdout.write(self.style.ERROR(f"Error for {user.email}: {e}"))
                return

        user.save()

    def check_pending_invitation(self, user):
        try:
            # Check for pending invitations using the admin client
            result = self.admin_client.admin_users_list(
                team_id=os.environ.get('SLACK_TEAM_ID'),
                limit=100
            )

            pending_invites = result.get('users', [])

            for invite in pending_invites:
                if invite.get('email') == user.email:
                    user.is_slack_invite_sent = True
                    user.is_slack_found_with_user_email = True
                    self.stdout.write(self.style.SUCCESS(f"Pending invitation found for {user.email}"))
                    return

            # If we get here, no pending invitation was found
            user.is_slack_invite_sent = False
            self.stdout.write(self.style.WARNING(f"No pending invitation found for {user.email}"))

        except SlackApiError as e:
            if e.response['error'] == 'ratelimited':
                # Handle rate limiting
                retry_after = int(e.response.headers.get('Retry-After', 30))
                self.stdout.write(self.style.WARNING(f"Rate limited. Waiting for {retry_after} seconds"))
                time.sleep(retry_after)
                # Retry the check for this user
                self.check_pending_invitation(user)
            else:
                self.stdout.write(self.style.ERROR(f"Error checking pending invitations: {e}"))
                user.is_slack_invite_sent = False

    def get_all_slack_users(self):
        users = []
        cursor = None
        while True:
            try:
                response = self.client.users_list(limit=200, cursor=cursor)
                users.extend(response['members'])
                cursor = response['response_metadata']['next_cursor']
                if not cursor:
                    break
                time.sleep(1)  # Wait for 1 second between pagination calls
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retry_after = int(e.response.headers.get('Retry-After', 30))
                    self.stdout.write(self.style.WARNING(f"Rate limited. Waiting for {retry_after} seconds"))
                    time.sleep(retry_after)
                else:
                    self.stdout.write(self.style.ERROR(f"Error fetching Slack users: {e}"))
                    break
        return users