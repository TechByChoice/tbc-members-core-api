import json

from django.db import models
from django_quill.fields import QuillField

from apps.core.models import CustomUser


# Create your models here.
class MentorSupportAreas(models.Model):
    name = models.CharField(max_length=116, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CommitmentLevel(models.Model):
    name = models.CharField(max_length=116)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ApplicationQuestion(models.Model):
    # Define choices for the 'question_type' field
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('quill', 'Quill'),
        ('boolean', 'Boolean'),
        ('array', 'Array'),
    ]
    # Define choices for the 'question_type' field
    QUESTION_GROUP_CHOICES = [
        ('career', 'Career'),
        ('mentorship', 'Mentorship'),
    ]

    question_text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_group = models.CharField(max_length=10, choices=QUESTION_GROUP_CHOICES)
    helper_text = models.TextField(max_length=255, blank=True, null=True)
    application_type = models.CharField(
        max_length=20,
        choices=[
            ('mentor_only', 'Mentor Only'),
            ('mentee_only', 'Mentee Only'),
            ('both', 'Both')
        ]
    )

    def __str__(self):
        return self.question_text


class ApplicationAnswers(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    question = models.ForeignKey(ApplicationQuestion, on_delete=models.CASCADE)

    # Use a JSONField to store various answer types
    answer = models.JSONField()

    @property
    def text_answer(self):
        return self.answer.get('text', '')

    @text_answer.setter
    def text_answer(self, answer_text):
        self.answer = {'text': answer_text}

    @property
    def boolean_answer(self):
        return self.answer.get('boolean', False)

    @boolean_answer.setter
    def boolean_answer(self, answer_boolean):
        self.answer = {'boolean': answer_boolean}

    @property
    def array_answer(self):
        return self.answer.get('array', [])

    @array_answer.setter
    def array_answer(self, answer_array):
        self.answer = {'array': answer_array}

    @property
    def quill_answer(self):
        return self.answer.get('quill', '')

    @quill_answer.setter
    def quill_answer(self, answer_quill):
        self.answer = {'quill': answer_quill}


class ValuesMatch(models.Model):
    value_power = models.IntegerField(blank=True, null=True)
    value_achievement = models.IntegerField(blank=True, null=True)
    value_hedonism = models.IntegerField(blank=True, null=True)
    value_stimulation = models.IntegerField(blank=True, null=True)
    value_self_direction = models.IntegerField(blank=True, null=True)
    value_universalism = models.IntegerField(blank=True, null=True)
    value_benevolence = models.IntegerField(blank=True, null=True)
    value_tradition = models.IntegerField(blank=True, null=True)
    value_conformity = models.IntegerField(blank=True, null=True)
    value_security = models.IntegerField(blank=True, null=True)


class MentorProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activated_at_date = models.DateTimeField(blank=True, null=True)
    interview_requested_at_date = models.DateTimeField(blank=True, null=True)
    paused_date = models.DateTimeField(blank=True, null=True)
    removed_date = models.DateTimeField(blank=True, null=True)
    removed_coc_date = models.DateTimeField(blank=True, null=True)
    removed_inactive_date = models.DateTimeField(blank=True, null=True)
    interview_reminder_date = models.DateTimeField(blank=True, null=True)
    mentor_support_areas = models.ManyToManyField(CommitmentLevel, blank=True)
    mentor_how_to_help = models.CharField(max_length=3000, blank=True, null=True)
    mentorship_goals = models.CharField(max_length=3000, blank=True, null=True)


class MenteeProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    #   Account Status
    # mentorship_status = models.CharField(max_length=18, choices=MENTORSHIP_STATUS, default=1)
    activated_at_date = models.DateTimeField(blank=True, null=True)
    interview_requested_at_date = models.DateTimeField(blank=True, null=True)
    paused_date = models.DateTimeField(blank=True, null=True)
    removed_date = models.DateTimeField(blank=True, null=True)
    removed_coc_date = models.DateTimeField(blank=True, null=True)
    removed_inactive_date = models.DateTimeField(blank=True, null=True)
    interview_reminder_date = models.DateTimeField(blank=True, null=True)
    mentee_support_areas = models.ManyToManyField(CommitmentLevel, blank=True)


class MentorRoster(models.Model):
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE)
    mentee = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE)
    mentee_review_of_mentor = QuillField(blank=True, null=True)
    mentor_review_of_mentee = QuillField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MentorshipProgramProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    calendar_link = models.URLField(null=True, blank=True, max_length=200)
    tbc_email = models.EmailField(null=True, blank=True, max_length=50)
    # Value based questions
    values = models.ForeignKey(ValuesMatch, on_delete=models.CASCADE, blank=True, null=True)
    # Mentor profile data
    mentor_profile = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, blank=True, null=True)
    # Mentee profile data
    mentee_profile = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE, blank=True, null=True)
    # Roster profile data
    roster = models.ForeignKey(MentorRoster, on_delete=models.CASCADE, blank=True, null=True)
    commitment_level = models.ManyToManyField(CommitmentLevel, related_name='commitment_level')
    # details
    biggest_strengths = models.CharField(max_length=3000, blank=True, null=True)
    career_success = models.CharField(max_length=3000, blank=True, null=True)
    career_milestones = models.CharField(max_length=3000, blank=True, null=True)
    career_goals = models.CharField(max_length=3000, blank=True, null=True)
    work_motivation = models.CharField(max_length=3000, blank=True, null=True)
    # Values
    value_power = models.IntegerField(blank=True, null=True)
    value_achievement = models.IntegerField(blank=True, null=True)
    value_hedonism = models.IntegerField(blank=True, null=True)
    value_stimulation = models.IntegerField(blank=True, null=True)
    value_self_direction = models.IntegerField(blank=True, null=True)
    value_universalism = models.IntegerField(blank=True, null=True)
    value_benevolence = models.IntegerField(blank=True, null=True)
    value_tradition = models.IntegerField(blank=True, null=True)
    value_conformity = models.IntegerField(blank=True, null=True)
    value_security = models.IntegerField(blank=True, null=True)


