# Generated by Django 4.1.3 on 2024-01-06 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mentorship", "0021_mentorshipprogramprofile_mentor_support_areas_and_more")
    ]

    operations = [
        migrations.RenameField(
            model_name="menteeprofile",
            old_name="commitment_level",
            new_name="mentee_commitment_level",
        ),
        migrations.RenameField(
            model_name="mentorprofile",
            old_name="commitment_level",
            new_name="mentor_commitment_level",
        ),
    ]
