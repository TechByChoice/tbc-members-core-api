# Generated by Django 4.2.13 on 2024-09-23 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_tracking_for_slack_users_found_slack_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='is_slack_active',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='is_slack_found_with_user_email',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='is_slack_invite_sent',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
