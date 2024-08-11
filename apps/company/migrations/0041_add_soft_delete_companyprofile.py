# Generated by Django 4.2.13 on 2024-08-03 01:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0040_certs_normalized_name_companytypes_normalized_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyprofile',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='companyprofile',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='job',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]