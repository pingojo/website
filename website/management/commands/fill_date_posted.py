from django.core.management.base import BaseCommand
from website.models import Job


class Command(BaseCommand):
    help = 'Updates posted_date to created_date for jobs where posted_date is null'

    def handle(self, *args, **kwargs):
        jobs_to_update = Job.objects.filter(posted_date__isnull=True)
        for job in jobs_to_update:
            job.posted_date = job.created
            job.save()
        self.stdout.write(self.style.SUCCESS(f'Updated {jobs_to_update.count()} jobs.'))
