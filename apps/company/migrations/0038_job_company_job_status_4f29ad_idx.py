# Generated by Django 4.2.13 on 2024-06-26 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0037_remove_certs_webflow_item_id_certs_details_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['status'], name='company_job_status_4f29ad_idx'),
        ),
    ]
