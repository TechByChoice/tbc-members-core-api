import logging
import os
import time
from typing import Dict, Any

import jwt
import requests
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class ZoomManager:
    BASE_URL = "https://api.zoom.us/v2"

    def __init__(self):
        self.api_key = os.getenv('ZOOM_API_KEY')
        self.api_secret = os.getenv('ZOOM_API_SECRET')
        self.user_id = os.getenv('ZOOM_USER_ID')  # The user ID or email of the Zoom account

        if not all([self.api_key, self.api_secret, self.user_id]):
            raise ImproperlyConfigured("Zoom API credentials are not properly set")

    def _get_token(self) -> str:
        """Generate a JWT token for Zoom API authentication."""
        token = jwt.encode(
            {
                'iss': self.api_key,
                'exp': time.time() + 3600  # Token expires in 1 hour
            },
            self.api_secret,
            algorithm='HS256'
        )
        return token

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Zoom API."""
        headers = {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json'
        }
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Zoom API request failed: {str(e)}")
            raise

    def create_meeting(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Zoom meeting.

        Args:
            event_data (dict): Dictionary containing event details.

        Returns:
            dict: Details of the created Zoom meeting.
        """
        endpoint = f"/users/{self.user_id}/meetings"
        meeting_data = {
            "topic": event_data['name']['html'],
            "type": 2,  # Scheduled meeting
            "start_time": event_data['start']['utc'],
            "duration": self._calculate_duration(event_data['start']['utc'], event_data['end']['utc']),
            "timezone": event_data['start']['timezone'],
            "agenda": event_data.get('description', {}).get('html', '')[:2000],  # Zoom has a 2000 char limit
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "watermark": False,
                "use_pmi": False,
                "approval_type": 0,
                "registration_type": 2,
                "audio": "both",
                "auto_recording": "cloud"
            }
        }

        logger.info(f"Creating Zoom meeting: {meeting_data['topic']}")
        return self._make_request("POST", endpoint, meeting_data)

    def create_webinar(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Zoom webinar.

        Args:
            event_data (dict): Dictionary containing event details.

        Returns:
            dict: Details of the created Zoom webinar.
        """
        endpoint = f"/users/{self.user_id}/webinars"
        webinar_data = {
            "topic": event_data['name']['html'],
            "type": 5,  # Webinar
            "start_time": event_data['start']['utc'],
            "duration": self._calculate_duration(event_data['start']['utc'], event_data['end']['utc']),
            "timezone": event_data['start']['timezone'],
            "agenda": event_data.get('description', {}).get('html', '')[:2000],
            "settings": {
                "host_video": True,
                "panelists_video": True,
                "practice_session": True,
                "hd_video": True,
                "approval_type": 0,
                "registration_type": 2,
                "audio": "both",
                "auto_recording": "cloud",
                "allow_multiple_devices": True
            }
        }

        logger.info(f"Creating Zoom webinar: {webinar_data['topic']}")
        return self._make_request("POST", endpoint, webinar_data)

    @staticmethod
    def _calculate_duration(start_time: str, end_time: str) -> int:
        """Calculate the duration of the event in minutes."""
        from dateutil.parser import parse
        start = parse(start_time)
        end = parse(end_time)
        duration = end - start
        return int(duration.total_seconds() / 60)
