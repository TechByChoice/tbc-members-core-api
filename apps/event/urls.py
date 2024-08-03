from django.urls import path
from .views import EventView, CreateEventView, EventRSVPView

urlpatterns = [
    path("", EventView.as_view(), name="events-list"),
    path("<str:event_id>/", EventView.as_view(), name="event-detail"),
    path("create/", CreateEventView.as_view(), name="create-event"),
    path("<str:event_id>/rsvp/", EventRSVPView.as_view(), name="event-rsvp"),
]