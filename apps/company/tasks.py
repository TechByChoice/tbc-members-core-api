import logging
from datetime import timedelta

from django.utils import timezone

from apps.company.models import Job
from api.celery import app

# Create a logger instance for the tasks
logger = logging.getLogger(__name__)


@app.task
def close_old_jobs():
    three_months_ago = timezone.now() - timedelta(days=90)
    jobs = Job.objects.filter(status="active", created_at__gte=three_months_ago)

    if jobs:
        print(f"We have {jobs.len} jobs that we'll expire today")
        for job in jobs:
            job.status = "job_expired"
            print(
                f"Marked {jobs.job_title} from {jobs.parent_company.company_name} as expired."
            )
        return True
    else:
        print(f"We don't have any jobs to expire today.")
