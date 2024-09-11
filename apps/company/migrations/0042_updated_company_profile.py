# Generated by Django 4.2.13 on 2024-09-11 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0041_add_soft_delete_companyprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyprofile',
            name='referral_connection_type',
            field=models.CharField(blank=True, choices=[('came_across_job', 'Came Across Job'), ('network_request', 'Someone in my network asked me to share this'), ('other', 'other')], max_length=15, null=True),
        ),
    ]