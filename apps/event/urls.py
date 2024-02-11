from django.urls import path
from .views import EventView

urlpatterns = [
    path("", EventView.as_view(), name="events-list"),
    path("<str:event_id>/", EventView.as_view(), name="event-detail"),
]
