import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize a Web client
slack_client = WebClient(token=os.environ['SLACK_API_TOKEN'])


def fetch_new_posts(channel_id, limit=10):
    """
    Fetch recent posts from a specified Slack channel.
    :param channel_id: The ID of the channel.
    :param limit: The maximum number of recent messages to fetch.
    :return: A list of recent messages.
    """
    try:
        response = slack_client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        return response['messages']
    except SlackApiError as e:
        print(f"Error fetching conversations: {e}")
        return None


def post_message(channel_id, text):
    """
    Post a message to a specified Slack channel.
    :param channel_id: The ID of the channel.
    :param text: The text of the message to post.
    :return: The response from the API.
    """
    try:
        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return response
    except SlackApiError as e:
        print(f"Error posting message: {e}")
        return None


def send_invite(email, channels):
    """
    Send an invite to a user to join the workspace.
    :param email: Email address of the user to invite.
    :param channels: List of channel IDs to invite the user to.
    :return: The response from the API.
    """
    try:
        response = slack_client.admin_inviteRequests_approve(
            email=email,
            channel_ids=channels
        )
        return response
    except SlackApiError as e:
        print(f"Error sending invite: {e}")
        return None

