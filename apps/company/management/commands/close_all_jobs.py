from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.company.models import Job

class Command(BaseCommand):
    help = 'Marks all jobs as expired in the database'

    def handle(self, *args, **options):
        jobs_updated = Job.objects.update(status='job_expired', updated_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f'Successfully closed {jobs_updated} jobs'))