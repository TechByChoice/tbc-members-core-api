# Generated by Django 4.1.3 on 2024-01-08 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mentorship", "0014_mentorshipprogramprofile_mentee_support_areas")
    ]

    operations = [
        migrations.AddField(
            model_name="mentorprofile",
            name="mentor_commitment_level",
            field=models.ManyToManyField(blank=True, to="mentorship.commitmentlevel"),
        ),
        migrations.AlterField(
            model_name="mentorprofile",
            name="mentor_support_areas",
            field=models.ManyToManyField(
                blank=True,
                related_name="mentor_support_areas",
                to="mentorship.mentorsupportareas",
            ),
        ),
    ]
