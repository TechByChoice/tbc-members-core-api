from django.db import models
from django_quill.fields import QuillField

from apps.core.models import CustomUser

# Create your models here.
CHOICES = ((None, "Prefer not to answer"), (True, "Yes"), (False, "No"))


class CommunityNeeds(models.Model):
    name = models.CharField(null=False, blank=False, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name


class MembersSpotlight(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.CharField(max_length=140, null=False)
    blog_link = models.URLField(max_length=200, null=False)
    is_email_sent = models.BooleanField(default=False)
    is_social_media_sent = models.BooleanField(default=False)
    twitter_post = QuillField(max_length=280, null=True, blank=True)
    facebook_post = QuillField(max_length=280, null=True, blank=True)
    ig_post = QuillField(max_length=280, null=True, blank=True)
    linkedin_post = QuillField(max_length=280, null=True, blank=True)
    profile_url = models.URLField(max_length=200)
    social_img_url = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " spotlight"
