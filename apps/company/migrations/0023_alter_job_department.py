# Generated by Django 4.1.3 on 2024-02-01 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0022_alter_companyprofile_industries_alter_job_skills")
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="department",
            field=models.ManyToManyField(blank=True, to="company.department"),
        )
    ]