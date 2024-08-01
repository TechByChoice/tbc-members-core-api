from django.core.management.base import BaseCommand

from apps.core.models import CustomUser
from apps.core.tasks import update_convertkit_tags_task


class Command(BaseCommand):
    help = 'Queue ConvertKit tag updates for all users'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        total_users = users.count()

        for i, user in enumerate(users, 1):
            update_convertkit_tags_task.delay(user.id)
            if i % 100 == 0:
                self.stdout.write(f"Queued {i}/{total_users} users")

        self.stdout.write(self.style.SUCCESS(f"Successfully queued tag updates for {total_users} users"))
