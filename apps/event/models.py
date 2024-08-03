from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models_programs import Program, Pillar

User = get_user_model()


class Event(models.Model):
    eventbrite_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    timezone = models.CharField(max_length=100)
    is_online = models.BooleanField(default=True)
    zoom_meeting_id = models.CharField(max_length=255, blank=True, null=True)
    zoom_webinar_id = models.CharField(max_length=255, blank=True, null=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, null=True)


class EventAttendee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    rsvp_date = models.DateTimeField(auto_now_add=True)
    ticket_type = models.CharField(max_length=100)
    is_attended = models.BooleanField(default=False)
