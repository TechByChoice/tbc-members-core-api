import os

from eventbrite import Eventbrite
from django.conf import settings

class EventbriteManager:
    def __init__(self):
        self.eventbrite = Eventbrite(os.environ.get('EVENTBRITE_OAUTH_TOKEN'))

    def create_event(self, event_data):
        # Assuming event_data is a dictionary containing event details
        return self.eventbrite.event_create(event_data)

    def update_event(self, event_id, event_data):
        return self.eventbrite.event_update(event_id, event_data)

    def publish_event(self, event_id):
        return self.eventbrite.event_publish(event_id)

    def cancel_event(self, event_id):
        return self.eventbrite.event_cancel(event_id)

    def delete_event(self, event_id):
        return self.eventbrite.event_delete(event_id)

    def get_all_events(self):
        # This will get the user's owned events, adjust as necessary
        return self.eventbrite.get('/organizations/291073217076/events?status=live')
