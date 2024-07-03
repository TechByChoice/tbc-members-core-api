# Generated by Django 4.2.13 on 2024-07-03 00:08

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0038_job_company_job_status_4f29ad_idx'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='created_by',
        ),
        migrations.AddField(
            model_name='job',
            name='created_by',
            field=models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
