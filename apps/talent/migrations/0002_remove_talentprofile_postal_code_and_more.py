# Generated by Django 4.1.3 on 2023-09-24 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talentprofile',
            name='postal_code',
        ),
        migrations.RemoveField(
            model_name='talentprofile',
            name='talent_search_active',
        ),
        migrations.AlterField(
            model_name='talentprofile',
            name='talent_status',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=3),
        ),
    ]
