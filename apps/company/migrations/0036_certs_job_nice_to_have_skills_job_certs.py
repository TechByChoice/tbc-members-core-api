# Generated by Django 4.2.11 on 2024-06-22 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("company", "0035_alter_job_external_description")]

    operations = [
        migrations.CreateModel(
            name="Certs",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=300)),
                (
                    "webflow_item_id",
                    models.CharField(blank=True, max_length=400, null=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name="job",
            name="nice_to_have_skills",
            field=models.ManyToManyField(
                blank=True, related_name="nice_to_have_skills", to="company.skill"
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="certs",
            field=models.ManyToManyField(blank=True, to="company.certs"),
        ),
    ]
