# Generated by Django 4.1.3 on 2023-09-26 05:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_userprofile_tbc_program_interest"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="instagram",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="twitter",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
