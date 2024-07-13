# Generated by Django 4.2.11 on 2024-06-01 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0020_customuser_is_open_doors_onboarding_complete")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="city",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="location",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="state",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
