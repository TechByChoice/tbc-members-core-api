# Generated by Django 4.1.3 on 2024-03-08 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_customuser_company_review_tokens_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_talent_choice",
            field=models.BooleanField(default=False),
        ),
    ]
