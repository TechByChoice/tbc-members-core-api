# Generated by Django 4.2.13 on 2024-10-18 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_allow_for_empty_states'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='last_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
