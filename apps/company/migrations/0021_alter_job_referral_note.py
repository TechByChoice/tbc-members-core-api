# Generated by Django 4.1.3 on 2023-12-25 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("company", "0020_remove_interviewrequest_candidate_and_more")]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="referral_note",
            field=models.TextField(blank=True, max_length=1000, null=True),
        )
    ]
