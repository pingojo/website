from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.template.defaultfilters import slugify
from website.models import Job, Company, Role, Application
from django.db.models import Count

class Command(BaseCommand):
    help = "Finds duplicate job entries and merges their related data"

    def handle(self, *args, **options):
        # Find duplicate jobs
        duplicate_jobs = (Job.objects.values("company__name", "role__title")
                          .annotate(count=Count('id'))
                          .order_by()
                          .filter(count__gt=1))

        for job in duplicate_jobs:
            # Get all jobs with this company and role
            jobs = Job.objects.filter(company__name=job["company__name"], role__title=job["role__title"])

            # Identify the primary job (the oldest one)
            primary_job = jobs.order_by('id').first()
            duplicate_jobs = jobs.exclude(id=primary_job.id)

            # Temporarily update the slug of duplicates to avoid IntegrityError
            for counter, dup_job in enumerate(duplicate_jobs, 1):
                if dup_job.link and not primary_job.link:
                    primary_job.link = dup_job.link
                if dup_job.description_markdown and not primary_job.description_markdown:
                    primary_job.description_markdown = dup_job.description_markdown

                if dup_job.location and not primary_job.location:
                    primary_job.location = dup_job.location
                if dup_job.salary_min and not primary_job.salary_min:
                    primary_job.salary_min = dup_job.salary_min
                if dup_job.salary_max and not primary_job.salary_max:
                    primary_job.salary_max = dup_job.salary_max
                if dup_job.job_type and not primary_job.job_type:
                    primary_job.job_type = dup_job.job_type
                if dup_job.remote and not primary_job.remote:
                    primary_job.remote = dup_job.remote
                if dup_job.created < primary_job.created:
                    primary_job.created = dup_job.created

                dup_job.slug = f"{primary_job.slug}-dup-{counter}"
                dup_job.save()

            # Attempt to save the primary job with the correct slug
            # Add a counter if a conflict occurs
            counter = 0
            while True:
                try:
                    #primary_job.slug = f'{slugify(primary_job.company.name)}-{slugify(primary_job.role.title)}-{counter}' if counter else f'{slugify(primary_job.company.name)}-{slugify(primary_job.role.title)}'
                    primary_job.slug = f'{slugify(primary_job.role.title + "-at-" + primary_job.company.name)}-{counter}' if counter else f'{slugify(primary_job.role.title + "-at-" + primary_job.company.name)}'
                    primary_job.save()
                    break
                except IntegrityError:
                    counter += 1

            # Transfer all related data to the primary job
            Application.objects.filter(job__in=duplicate_jobs).update(job=primary_job)

            # Delete duplicate jobs
            duplicate_jobs.delete()
