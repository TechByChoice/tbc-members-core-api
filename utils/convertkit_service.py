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
        # print(add_tags, remove_tags, email)
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

    def _remove_tags_from_subscriber(self, email, tags):
        for tag_name in tags:
            print("Removing subscriber tags: {}".format(tag_name))
            tag = EmailTags.objects.filter(name__iexact=tag_name).first()
            if tag:
                self._make_api_call_with_retry(f'tags/{tag.convert_tag_kit_id}/unsubscribe', {'email': email})

    def _make_api_call_with_retry(self, endpoint, data, max_retries=3, delay=5):
        for attempt in range(max_retries):
            try:
                return self._make_api_call(endpoint, data)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = self._get_retry_after(e.response) or delay
                    time.sleep(wait_time)
                else:
                    raise

    def _make_api_call(self, endpoint, data):
        url = f'{self.BASE_URL}{endpoint}'
        params = {'api_secret': self.api_secret}
        response = requests.post(url, json=data, params=params)
        response.raise_for_status()
        return response

    def _get_retry_after(self, response):
        retry_after = response.headers.get('Retry-After')
        return int(retry_after) if retry_after and retry_after.isdigit() else None