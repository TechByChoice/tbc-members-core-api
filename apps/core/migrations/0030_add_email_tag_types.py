# Generated by Django 4.2.13 on 2024-07-31 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_add_email_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtags',
            name='type',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
