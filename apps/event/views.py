import logging

from django.core.exceptions import BadRequest
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models_programs import Program, Pillar
from apps.event.models import Event, EventAttendee
from utils.zoom_utils import ZoomManager

from utils.eventbrite import EventbriteManager
from utils.logging_helper import log_exception, timed_function

logger = logging.getLogger(__name__)


class EventView(View):
    def get(self, request, *args, **kwargs):
        event_id = kwargs.get("event_id")
        manager = EventbriteManager()

        if event_id:
            # Get one specific event
            try:
                event = manager.eventbrite.get_event(event_id)
                return JsonResponse(event)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=404)
        else:
            # Get all events
            try:
                events = manager.get_all_events()
                return JsonResponse(
                    events, safe=False
                )  # Note the safe=False for non-dict objects
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


class CreateEventView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request):
        try:
            event_data = self.validate_event_data(request.data)

            # Create Zoom meeting or webinar
            zoom_manager = ZoomManager()
            if event_data['is_webinar']:
                zoom_event = zoom_manager.create_webinar(event_data)
                zoom_id = zoom_event['id']
                zoom_join_url = zoom_event['join_url']
            else:
                zoom_event = zoom_manager.create_meeting(event_data)
                zoom_id = zoom_event['id']
                zoom_join_url = zoom_event['join_url']

            # Add Zoom details to Eventbrite event data
            event_data['online_event'] = {
                'type': 'zoom',
                'url': zoom_join_url
            }

            # Create Eventbrite event
            eventbrite_manager = EventbriteManager()
            eventbrite_event = eventbrite_manager.create_event(event_data)

            # Save event in our database
            program = Program.objects.get(id=event_data['program_id'])
            pillar = Pillar.objects.get(id=event_data['pillar_id'])

            event = Event.objects.create(
                eventbrite_id=eventbrite_event['id'],
                name=event_data['name']['html'],
                description=event_data['description']['html'],
                start_time=event_data['start']['utc'],
                end_time=event_data['end']['utc'],
                timezone=event_data['start']['timezone'],
                is_online=True,
                zoom_meeting_id=None if event_data['is_webinar'] else zoom_id,
                zoom_webinar_id=zoom_id if event_data['is_webinar'] else None,
                program=program,
                pillar=pillar
            )

            logger.info(f"Event created successfully. Event ID: {event.id}")
            return Response({
                "status": "success",
                "message": "Event created successfully",
                "event": {
                    "id": event.id,
                    "eventbrite_id": event.eventbrite_id,
                    "zoom_id": zoom_id,
                    "zoom_join_url": zoom_join_url
                }
            }, status=status.HTTP_201_CREATED)

        except ValidationError as ve:
            logger.warning(f"Validation error in event creation: {str(ve)}")
            return Response({
                "status": "error",
                "message": str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in event creation: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "An unexpected error occurred while creating the event."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_event_data(self, data):
        required_fields = ['name', 'start', 'end', 'currency', 'program_id', 'pillar_id', 'is_webinar']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Additional validation...

        return data


class EventRSVPView(APIView):
    permission_classes = [IsAuthenticated]

    @log_exception(logger)
    @timed_function(logger)
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            ticket_type = request.data.get('ticket_type', 'general')

            # Create RSVP in Eventbrite
            eventbrite_manager = EventbriteManager()
            eventbrite_order = eventbrite_manager.create_order(event.eventbrite_id, request.user, ticket_type)

            # Save RSVP in our database
            EventAttendee.objects.create(
                user=request.user,
                event=event,
                ticket_type=ticket_type
            )

            logger.info(f"User {request.user.id} RSVPed to event {event_id}")
            return Response({
                "status": "success",
                "message": "RSVP successful",
                "order_id": eventbrite_order['id']
            }, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            logger.warning(f"Attempted RSVP to non-existent event: {event_id}")
            return Response({
                "status": "error",
                "message": "Event not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error in RSVP process: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "An error occurred while processing your RSVP"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
