# Generated by Django 4.2.11 on 2024-05-12 02:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0026_companyprofile_city_companyprofile_postal_code_and_more")
    ]

    operations = [
        migrations.AddField(
            model_name="companyprofile",
            name="coresignal_id",
            field=models.CharField(blank=True, max_length=60, null=True),
        )
    ]
