# Generated by Django 4.1.3 on 2024-01-07 15:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="ApplicationQuestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question_text", models.CharField(max_length=255)),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("quill", "Quill"),
                            ("boolean", "Boolean"),
                            ("array", "Array"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "question_group",
                    models.CharField(
                        choices=[("career", "Career"), ("mentorship", "Mentorship")],
                        max_length=10,
                    ),
                ),
                (
                    "helper_text",
                    models.TextField(blank=True, max_length=255, null=True),
                ),
                (
                    "application_type",
                    models.CharField(
                        choices=[
                            ("mentor_only", "Mentor Only"),
                            ("mentee_only", "Mentee Only"),
                            ("both", "Both"),
                        ],
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CommitmentLevel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=116)),
                ("created_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="MenteeProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("activated_at_date", models.DateTimeField(blank=True, null=True)),
                (
                    "interview_requested_at_date",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("paused_date", models.DateTimeField(blank=True, null=True)),
                ("removed_date", models.DateTimeField(blank=True, null=True)),
                ("removed_coc_date", models.DateTimeField(blank=True, null=True)),
                ("removed_inactive_date", models.DateTimeField(blank=True, null=True)),
                (
                    "interview_reminder_date",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "commitment_level",
                    models.ManyToManyField(blank=True, to="mentorship.commitmentlevel"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MentorProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "mentor_status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("active", "Active"),
                            ("interviewing", "Interviewing"),
                            ("paused", "Paused"),
                            ("need_cal_info", "Need Booking Info"),
                            ("removed", "Removed"),
                            ("removed_coc_issues", "Removed COC Issues"),
                            ("removed_inactive", "Removed Inactive"),
                            ("incomplete_application", "Incomplete Application"),
                            ("lacking_experience", "Lacking Skill or Experience"),
                            ("rejected_other", "Other"),
                            ("passed_interview", "Passed Interview"),
                        ],
                        default=1,
                        max_length=22,
                    ),
                ),
                ("activated_at_date", models.DateTimeField(blank=True, null=True)),
                (
                    "interview_requested_at_date",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("paused_date", models.DateTimeField(blank=True, null=True)),
                ("removed_date", models.DateTimeField(blank=True, null=True)),
                ("removed_coc_date", models.DateTimeField(blank=True, null=True)),
                ("removed_inactive_date", models.DateTimeField(blank=True, null=True)),
                (
                    "interview_reminder_date",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "mentor_how_to_help",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "mentorship_goals",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "mentor_commitment_level",
                    models.ManyToManyField(blank=True, to="mentorship.commitmentlevel"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MentorReview",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rating", models.IntegerField()),
                (
                    "review_author",
                    models.CharField(
                        choices=[("mentor", "Mentor"), ("mentee", "Mentee")],
                        max_length=6,
                    ),
                ),
                (
                    "review_content",
                    models.TextField(blank=True, max_length=1000, null=True),
                ),
                (
                    "mentee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.menteeprofile",
                    ),
                ),
                (
                    "mentor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.mentorprofile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MentorRoster",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "mentee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.menteeprofile",
                    ),
                ),
                (
                    "mentee_review_of_mentor",
                    models.ManyToManyField(
                        blank=True,
                        related_name="mentee_reviews",
                        to="mentorship.mentorreview",
                    ),
                ),
                (
                    "mentor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.mentorprofile",
                    ),
                ),
                (
                    "mentor_review_of_mentee",
                    models.ManyToManyField(
                        blank=True,
                        related_name="mentor_reviews",
                        to="mentorship.mentorreview",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MentorSupportAreas",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=116)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ValuesMatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("value_power", models.IntegerField(blank=True, null=True)),
                ("value_achievement", models.IntegerField(blank=True, null=True)),
                ("value_hedonism", models.IntegerField(blank=True, null=True)),
                ("value_stimulation", models.IntegerField(blank=True, null=True)),
                ("value_self_direction", models.IntegerField(blank=True, null=True)),
                ("value_universalism", models.IntegerField(blank=True, null=True)),
                ("value_benevolence", models.IntegerField(blank=True, null=True)),
                ("value_tradition", models.IntegerField(blank=True, null=True)),
                ("value_conformity", models.IntegerField(blank=True, null=True)),
                ("value_security", models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("note", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="MenteeMentorConnections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "mentor_mentee_connection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="MenteeMentorConnections",
                        to="mentorship.mentorroster",
                    ),
                ),
                ("reason", models.ManyToManyField(to="mentorship.mentorsupportareas")),
            ],
        ),
        migrations.CreateModel(
            name="MentorshipProgramProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("calendar_link", models.URLField(blank=True, null=True)),
                ("tbc_email", models.EmailField(blank=True, max_length=50, null=True)),
                (
                    "biggest_strengths",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "career_success",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "career_milestones",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "career_goals",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                (
                    "work_motivation",
                    models.CharField(blank=True, max_length=3000, null=True),
                ),
                ("value_power", models.IntegerField(blank=True, null=True)),
                ("value_achievement", models.IntegerField(blank=True, null=True)),
                ("value_hedonism", models.IntegerField(blank=True, null=True)),
                ("value_stimulation", models.IntegerField(blank=True, null=True)),
                ("value_self_direction", models.IntegerField(blank=True, null=True)),
                ("value_universalism", models.IntegerField(blank=True, null=True)),
                ("value_benevolence", models.IntegerField(blank=True, null=True)),
                ("value_tradition", models.IntegerField(blank=True, null=True)),
                ("value_conformity", models.IntegerField(blank=True, null=True)),
                ("value_security", models.IntegerField(blank=True, null=True)),
                (
                    "commitment_level",
                    models.ManyToManyField(
                        related_name="commitment_level", to="mentorship.commitmentlevel"
                    ),
                ),
                (
                    "mentee_profile",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.menteeprofile",
                    ),
                ),
                (
                    "mentee_support_areas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="mentee_support_areas",
                        to="mentorship.mentorsupportareas",
                    ),
                ),
                (
                    "mentor_profile",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.mentorprofile",
                    ),
                ),
                (
                    "mentor_support_areas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="mentor_support_areas",
                        to="mentorship.mentorsupportareas",
                    ),
                ),
                (
                    "roster",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.mentorroster",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "values",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.valuesmatch",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="mentorroster",
            name="sessions",
            field=models.ManyToManyField(
                related_name="mentor_roster_sessions", to="mentorship.session"
            ),
        ),
        migrations.AddField(
            model_name="menteeprofile",
            name="mentee_support_areas",
            field=models.ManyToManyField(
                blank=True, to="mentorship.mentorsupportareas"
            ),
        ),
        migrations.AddField(
            model_name="menteeprofile",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.CreateModel(
            name="ApplicationAnswers",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("answer", models.JSONField()),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mentorship.applicationquestion",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
