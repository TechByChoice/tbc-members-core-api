from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from utils.eventbrite import EventbriteManager


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
