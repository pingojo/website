from django.core.management.base import BaseCommand
from django.db.models import Max, Min
from website.models import Job, Application, Email

class Command(BaseCommand):
    help = 'Combines duplicate Applications of each unique Job'

    def handle(self, *args, **options):
        # Get all jobs
        jobs = Job.objects.all()

        for job in jobs:
            # Get all applications for the current job
            applications = Application.objects.filter(job=job)
            application_count = applications.count()

            # Skip if there are not multiple applications for the current job
            if application_count <= 1:
                continue

            self.stdout.write(
                f"Found {application_count} applications for job with ID {job.id} and slug {job.slug}")

            # Get the earliest date_applied, latest stage, and most recent date_of_last_email
            earliest_date_applied = applications.aggregate(Min('date_applied'))['date_applied__min']
            latest_stage = applications.latest('date_applied').stage
            most_recent_date_of_last_email = applications.aggregate(Max('date_of_last_email'))['date_of_last_email__max']

            # Create a new application
            new_application = Application(user=applications.first().user,
                                          company=job.company,
                                          job=job,
                                          date_applied=earliest_date_applied,
                                          stage=latest_stage,
                                          date_of_last_email=most_recent_date_of_last_email)

            new_application.save()

            # Reassign emails from old applications to new application
            Email.objects.filter(application__in=applications).update(application=new_application)

            refresh_applications = Application.objects.filter(job=job).exclude(id=new_application.id)
            refresh_applications.delete()

            self.stdout.write(f"Applications combined for job with ID {job.id} and slug {job.slug}")

        self.stdout.write(self.style.SUCCESS('Successfully combined Applications.'))
