from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import logging
from django.core.cache import cache
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from utils.eventbrite import EventbriteManager

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
@permission_classes([AllowAny])
class EventView(View):
    def get(self, request, *args, **kwargs):
        event_id = kwargs.get("event_id")
        manager = EventbriteManager()

        # Check if this is a request for the latest event
        if request.path.endswith('/latest/'):
            try:
                # Try to get cached latest event
                cache_key = 'latest_event'
                cached_event = cache.get(cache_key)
                
                if cached_event:
                    logger.info("Serving cached latest event")
                    return JsonResponse(cached_event)
                
                # If not cached, fetch from Eventbrite
                event = manager.get_upcoming_events()
                if not event:
                    return JsonResponse(
                        {"error": "No upcoming events found"}, 
                        status=404
                    )
                
                # Format the response data
                event_data = {
                    'id': event.get('id'),
                    'name': event.get('name', {}).get('text'),
                    'speaker': None,
                    'description': event.get('description', {}).get('text'),
                    'url': event.get('url'),
                    'start': event.get('start', {}).get('local'),
                    'end': event.get('end', {}).get('local'),
                    'capacity': event.get('capacity'),
                    'status': event.get('status'),
                    'image_url': event.get('logo', {}).get('url') if event.get('logo') else None,
                    'online_event': event.get('online_event', False),
                    'type': 'online' if event.get('online_event', False) else 'in_person',
                }

                # Handle venue information
                if event.get('online_event'):
                    event_data['venue'] = 'Zoom'
                else:
                    venue_id = event.get('venue_id')
                    if venue_id:
                        try:
                            venue = manager.eventbrite.get_venue(venue_id)
                            event_data['venue'] = {
                                'name': venue.get('name'),
                                'address': {
                                    'address_1': venue.get('address', {}).get('address_1'),
                                    'address_2': venue.get('address', {}).get('address_2'),
                                    'city': venue.get('address', {}).get('city'),
                                    'region': venue.get('address', {}).get('region'),
                                    'postal_code': venue.get('address', {}).get('postal_code'),
                                    'country': venue.get('address', {}).get('country'),
                                }
                            }
                        except Exception as e:
                            logger.error(f"Error fetching venue details: {str(e)}")
                            event_data['venue'] = None
                    else:
                        event_data['venue'] = None
                
                # Cache the event data for 1 hour
                cache.set(cache_key, event_data, 3600)
                
                return JsonResponse(event_data)
            except Exception as e:
                logger.error(f"Error fetching latest event: {str(e)}")
                return JsonResponse(
                    {"error": "Failed to fetch latest event"}, 
                    status=500
                )

        # Original code for other event endpoints
        if event_id:
            try:
                event = manager.eventbrite.get_event(event_id)
                return JsonResponse(event)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=404)
        else:
            try:
                events = manager.get_all_events()
                return JsonResponse(events, safe=False)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

    def post(self, request, *args, **kwargs):
        # Create a new event
        try:
            event_data = request.POST  # or parse as JSON
            manager = EventbriteManager()
            event = manager.create_event(event_data)
            return JsonResponse(event, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def put(self, request, *args, **kwargs):
        # Edit an existing event
        event_id = kwargs.get("event_id")
        if not event_id:
            raise BadRequest("Event ID is required.")

        try:
            event_data = request.POST  # or parse as JSON
            manager = EventbriteManager()
            event = manager.update_event(event_id, event_data)
            return JsonResponse(event, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def delete(self, request, *args, **kwargs):
        # Delete an event
        event_id = kwargs.get("event_id")
        if not event_id:
            raise BadRequest("Event ID is required.")

        try:
            manager = EventbriteManager()
            manager.delete_event(event_id)
            return JsonResponse({"status": "Deleted"}, status=204)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
