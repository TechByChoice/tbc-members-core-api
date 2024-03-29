# Generated by Django 4.1.13 on 2024-02-12 02:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_alter_userprofile_tbc_program_interest"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="company_review_tokens",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="customuser",
            name="is_company_review_access_active",
            field=models.BooleanField(default=False),
        ),
    ]
