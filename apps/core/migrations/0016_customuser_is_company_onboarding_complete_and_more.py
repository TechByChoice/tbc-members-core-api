# Generated by Django 4.1.13 on 2024-03-09 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_userprofile_identity_ethic_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_company_onboarding_complete",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="is_email_confirmation_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="is_email_confirmed",
            field=models.BooleanField(default=False),
        ),
    ]