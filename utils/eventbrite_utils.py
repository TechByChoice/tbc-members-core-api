import logging
import os
from typing import Dict, Any

from django.core.exceptions import ImproperlyConfigured

from eventbrite import Eventbrite

logger = logging.getLogger(__name__)


class EventbriteManager:
    def __init__(self):
        self.oauth_token = os.getenv('EVENTBRITE_OAUTH_TOKEN')
        if not self.oauth_token:
            raise ImproperlyConfigured("Eventbrite OAuth token is not set")
        self.eb_client = Eventbrite(self.oauth_token)
        self.organization_id = self._get_organization_id()

    def _get_organization_id(self) -> str:
        """Retrieve the organization ID for the authenticated user."""
        try:
            user_info = self.eb_client.get_user()
            return user_info['organizations'][0]['id']
        except Exception as e:
            logger.error(f"Failed to retrieve Eventbrite organization ID: {str(e)}")
            raise

    @staticmethod
    def _format_event_data(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the event data for Eventbrite API."""
        formatted_data = {
            "event": {
                "name": {
                    "html": event_data['name']
                },
                "description": {
                    "html": event_data.get('description', '')
                },
                "start": {
                    "timezone": event_data['timezone'],
                    "utc": event_data['start_time']
                },
                "end": {
                    "timezone": event_data['timezone'],
                    "utc": event_data['end_time']
                },
                "currency": event_data.get('currency', 'USD'),
                "online_event": event_data.get('is_online', False),
                "listed": event_data.get('is_listed', True),
                "shareable": event_data.get('is_shareable', True),
                "invite_only": event_data.get('is_invite_only', False),
                "show_remaining": event_data.get('show_remaining', True),
                "capacity": event_data.get('capacity', 100),
            }
        }

        if event_data.get('is_online', False):
            formatted_data['event']['online_event'] = True
            if 'online_event_url' in event_data:
                formatted_data['event']['online_event_page'] = {
                    "url": event_data['online_event_url'],
                    "type": "other"
                }

        return formatted_data

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an Eventbrite event.

        Args:
            event_data (dict): Dictionary containing event details.

        Returns:
            dict: Details of the created Eventbrite event.
        """
        try:
            formatted_data = self._format_event_data(event_data)
            event = self.eb_client.event_create(self.organization_id, **formatted_data)
            logger.info(f"Created Eventbrite event: {event['id']}")
            return event
        except Exception as e:
            logger.error(f"Failed to create Eventbrite event: {str(e)}")
            raise

    def create_ticket_class(self, event_id: str, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a ticket class for an Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event.
            ticket_data (dict): Dictionary containing ticket details.

        Returns:
            dict: Details of the created ticket class.
        """
        try:
            ticket_class = self.eb_client.ticket_class_create(event_id, **ticket_data)
            logger.info(f"Created ticket class for event {event_id}: {ticket_class['id']}")
            return ticket_class
        except Exception as e:
            logger.error(f"Failed to create ticket class for event {event_id}: {str(e)}")
            raise

    def create_order(self, event_id: str, user: Any, ticket_type: str) -> Dict[str, Any]:
        """
        Create an order (RSVP) for an Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event.
            user (User): The user object of the person making the order.
            ticket_type (str): The type of ticket being ordered.

        Returns:
            dict: Details of the created order.
        """
        try:
            # First, get the ticket class ID
            ticket_classes = self.eb_client.get_event_ticket_classes(event_id)
            ticket_class_id = next((tc['id'] for tc in ticket_classes['ticket_classes'] if tc['name'] == ticket_type),
                                   None)

            if not ticket_class_id:
                raise ValueError(f"Ticket type '{ticket_type}' not found for event {event_id}")

            # Create the order
            order_data = {
                "event_id": event_id,
                "attendees": [
                    {
                        "profile": {
                            "name": f"{user.first_name} {user.last_name}",
                            "email": user.email,
                        },
                        "answers": [],  # Add any custom questions/answers here
                        "ticket_class_id": ticket_class_id,
                    }
                ],
            }

            order = self.eb_client.create_order(order_data)
            logger.info(f"Created order for event {event_id}, user {user.id}: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Failed to create order for event {event_id}, user {user.id}: {str(e)}")
            raise

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        Retrieve details of an Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event.

        Returns:
            dict: Details of the Eventbrite event.
        """
        try:
            event = self.eb_client.get_event(event_id)
            logger.info(f"Retrieved Eventbrite event: {event_id}")
            return event
        except Exception as e:
            logger.error(f"Failed to retrieve Eventbrite event {event_id}: {str(e)}")
            raise

    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event to update.
            event_data (dict): Dictionary containing updated event details.

        Returns:
            dict: Details of the updated Eventbrite event.
        """
        try:
            formatted_data = self._format_event_data(event_data)
            event = self.eb_client.event_update(event_id, **formatted_data)
            logger.info(f"Updated Eventbrite event: {event_id}")
            return event
        except Exception as e:
            logger.error(f"Failed to update Eventbrite event {event_id}: {str(e)}")
            raise

    def cancel_event(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel an Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event to cancel.

        Returns:
            dict: Response from the Eventbrite API.
        """
        try:
            response = self.eb_client.event_cancel(event_id)
            logger.info(f"Cancelled Eventbrite event: {event_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel Eventbrite event {event_id}: {str(e)}")
            raise

    def get_attendees(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the list of attendees for an Eventbrite event.

        Args:
            event_id (str): The ID of the Eventbrite event.

        Returns:
            list: List of dictionaries containing attendee details.
        """
        try:
            attendees = self.eb_client.get_event_attendees(event_id)
            logger.info(f"Retrieved attendees for Eventbrite event: {event_id}")
            return attendees['attendees']
        except Exception as e:
            logger.error(f"Failed to retrieve attendees for Eventbrite event {event_id}: {str(e)}")
            raise
