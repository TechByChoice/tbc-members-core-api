# Generated by Django 4.1.3 on 2023-11-29 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("mentorship", "0010_menteeprofile_mentor_how_to_help_and_more")]

    operations = [
        migrations.RemoveField(model_name="menteeprofile", name="mentor_how_to_help"),
        migrations.RemoveField(model_name="menteeprofile", name="mentorship_goals"),
        migrations.AddField(
            model_name="mentorprofile",
            name="mentor_how_to_help",
            field=models.CharField(blank=True, max_length=3000, null=True),
        ),
        migrations.AddField(
            model_name="mentorprofile",
            name="mentorship_goals",
            field=models.CharField(blank=True, max_length=3000, null=True),
        ),
    ]