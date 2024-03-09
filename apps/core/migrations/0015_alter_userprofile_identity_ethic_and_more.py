# Generated by Django 4.1.3 on 2024-03-09 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_customuser_is_talent_choice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="identity_ethic",
            field=models.ManyToManyField(
                blank=True,
                related_name="userprofile_identity_ethic",
                to="core.ethicidentities",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="identity_gender",
            field=models.ManyToManyField(
                blank=True,
                related_name="userprofile_identity_gender",
                to="core.genderidentities",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="identity_pronouns",
            field=models.ManyToManyField(
                blank=True,
                related_name="userprofile_identity_pronouns",
                to="core.pronounsidentities",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="identity_sexuality",
            field=models.ManyToManyField(
                blank=True,
                related_name="userprofile_identity_sexuality",
                to="core.sexualidentities",
            ),
        ),
    ]