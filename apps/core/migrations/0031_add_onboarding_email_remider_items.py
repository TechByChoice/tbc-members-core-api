# Generated by Django 4.2.13 on 2024-08-02 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_add_email_tag_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_onboarding_reminder_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='onboarding_reminder_sent_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
