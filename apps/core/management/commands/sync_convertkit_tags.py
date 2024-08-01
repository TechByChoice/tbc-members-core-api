import os

from django.core.management.base import BaseCommand
from django.conf import settings
import requests

from apps.core.models import EmailTags


class Command(BaseCommand):
    help = 'Sync ConvertKit tags with the EmailTags model'

    def handle(self, *args, **options):
        api_secret = os.getenv("CONVERTKIT_API_SECRET_KEY")
        url = f'https://api.convertkit.com/v3/tags?api_secret={api_secret}'

        try:
            response = requests.get(url)
            response.raise_for_status()
            tags_data = response.json().get('tags', [])

            for tag in tags_data:
                EmailTags.objects.update_or_create(
                    convert_tag_kit_id=tag['id'],
                    defaults={'name': tag['name']}
                )

            self.stdout.write(self.style.SUCCESS(f'Successfully synced {len(tags_data)} tags'))
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Failed to sync tags: {str(e)}'))