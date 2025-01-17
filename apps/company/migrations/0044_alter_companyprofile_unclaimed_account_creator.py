# Generated by Django 4.2.13 on 2024-10-19 02:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def preserve_unclaimed_account_creator(apps, schema_editor):
    CompanyProfile = apps.get_model('company', 'CompanyProfile')
    for profile in CompanyProfile.objects.all():
        if profile.unclaimed_account_creator_id:
            profile.new_unclaimed_account_creator_id = profile.unclaimed_account_creator_id
            profile.save()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0043_alter_companyprofile_account_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyprofile',
            name='new_unclaimed_account_creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile_as_unclaimed_account_creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(preserve_unclaimed_account_creator),
        migrations.RemoveField(
            model_name='companyprofile',
            name='unclaimed_account_creator',
        ),
        migrations.RenameField(
            model_name='companyprofile',
            old_name='new_unclaimed_account_creator',
            new_name='unclaimed_account_creator',
        ),
    ]