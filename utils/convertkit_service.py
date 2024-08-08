import os
import requests
import time
from django.core.cache import cache

from apps.core.models import EmailTags


class ConvertKitService:
    BASE_URL = 'https://api.convertkit.com/v3/'

    def __init__(self):
        self.api_key = os.getenv("CONVERTKIT_API_KEY")
        self.api_secret = os.getenv("CONVERTKIT_API_SECRET_KEY")

    def update_subscriber_tags(self, email, add_tags=None, remove_tags=None):
        print("Updating subscriber tags")
        print(add_tags, remove_tags)
        if add_tags:
            print("Adding ...")
            self._add_tags_to_subscriber(email, add_tags)
            print("Added subscriber tags")
        if remove_tags:
            print("Removing ...")
            self._remove_tags_from_subscriber(email, remove_tags)
            print("Removed subscriber tags")

    def _add_tags_to_subscriber(self, email, tags):
        print("Adding subscriber tags: {}".format(tags))
        for tag_name in tags:
            tag = EmailTags.objects.filter(name__iexact=tag_name).first()
            if tag:
                self._make_api_call_with_retry(f'tags/{tag.convert_tag_kit_id}/subscribe', {'email': email})

    def get_subscriber_tags(self, email):
        """
        Fetch all tags associated with a subscriber's email address.

        :param email: The email address of the subscriber
        :return: A list of tag names associated with the subscriber
        """
        print("Getting subscriber tags")
        subscriber_id = self._get_subscriber_id(email)
        print("Subscriber id: {}".format(subscriber_id))

        if subscriber_id is None:
            print("No subscriber found, returning no tags")
            return []

        # Now, get the tags for this subscriber
        response = self._make_api_call(
            f'subscribers/{subscriber_id}/tags?api_key={self.api_secret}',
            {'email': email},
            is_get=True
        )
        response.raise_for_status()
        tags_data = response.json()
        print("Got tags data: {}".format(tags_data))
        # Extract and return the tag names
        return [tag["name"] for tag in tags_data.get("tags", [])]

    def _get_subscriber_id(self, email):
        """
        Fetch the subscriber user id

        :param email: The email address of the subscriber
        :return: id associated with the subscriber
        """
        print("Getting subscriber id for user")
        response = self._make_api_call(f'subscribers?api_secret={self.api_secret}', {'email_address': email}, True)
        response.raise_for_status()
        subscriber_data = response.json()

        if not subscriber_data.get("subscribers"):
            print("Subscriber not found")
            return []

        subscriber_id = subscriber_data["subscribers"][0]["id"]
        return subscriber_id

    def _remove_tags_from_subscriber(self, email, tags):
        for tag_name in tags:
            print("Removing subscriber tags: {}".format(tag_name))
            tag = EmailTags.objects.filter(name__iexact=tag_name).first()
            if tag:
                self._make_api_call_with_retry(f'tags/{tag.convert_tag_kit_id}/unsubscribe', {'email': email})

    def _make_api_call_with_retry(self, endpoint, data, max_retries=3, delay=10):
        for attempt in range(max_retries):
            try:
                return self._make_api_call(endpoint, data)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = self._get_retry_after(e.response) or delay
                    time.sleep(wait_time)
                else:
                    raise

    def _make_api_call(self, endpoint, data, is_get=False):
        url = f'{self.BASE_URL}{endpoint}'
        params = {'api_secret': self.api_secret}
        if is_get:
            response = requests.get(url, json=data, params=params)
        else:
            response = requests.post(url, json=data, params=params)
        response.raise_for_status()
        return response

    def _get_retry_after(self, response):
        retry_after = response.headers.get('Retry-After')
        return int(retry_after) if retry_after and retry_after.isdigit() else None
