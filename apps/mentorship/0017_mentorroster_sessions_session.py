# Generated by Django 4.1.3 on 2024-01-04 23:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mentorship", "0016_alter_mentorprofile_mentor_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="mentorroster",
            name="sessions",
            field=models.ManyToManyField(
                related_name="sessions", to="mentorship.mentorreview"
            ),
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
    ]
