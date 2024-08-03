from django.db import models
from django_quill.fields import QuillField

from apps.core.models import CustomUser

# Create your models here.
CHOICES = ((None, "Prefer not to answer"), (True, "Yes"), (False, "No"))


class Pillar(models.Model):
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Program(models.Model):
    name = models.CharField(max_length=255)
    pillars = models.ManyToManyField(Pillar)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
