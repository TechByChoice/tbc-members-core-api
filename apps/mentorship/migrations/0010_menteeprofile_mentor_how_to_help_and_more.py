# Generated by Django 4.1.3 on 2023-11-29 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mentorship", "0009_remove_mentorprofile_mentor_support_areas_and_more")
    ]

    operations = [
        migrations.AddField(
            model_name="menteeprofile",
            name="mentor_how_to_help",
            field=models.CharField(blank=True, max_length=3000, null=True),
        ),
        migrations.AddField(
            model_name="menteeprofile",
            name="mentorship_goals",
            field=models.CharField(blank=True, max_length=3000, null=True),
        ),
    ]
