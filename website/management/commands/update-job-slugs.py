from django.core.management.base import BaseCommand
from django.utils.text import slugify
from website.models import Job, Role

class Command(BaseCommand):
    help = "Updates job slugs"

    def handle(self, *args, **options):
        jobs = Job.objects.all().order_by('id')

        for job in jobs:
            
            new_slug = None
            if job.role:
                if job.role.title:
                    new_slug = slugify(f"{job.role.title}-at-{job.company.name}")

            else:

                if job.title is not "":
                    if " at " in job.title:
                        role_part_of_title = job.title.split(" at ")[0]
                    else:
                        role_part_of_title = job.title
                        
                    role_slug = slugify(role_part_of_title[:50])
                    role, _ = Role.objects.get_or_create(
                            slug=role_slug, defaults={"title": role_part_of_title}
                    )

                    
                    job.role = role
                    job.save()
                    new_slug = slugify(f"{job.role.title}-at-{job.company.name}")
                    
                
            if new_slug:
                if Job.objects.filter(slug=new_slug).exists():
                    jobs_for_that_company = Job.objects.filter(company=job.company).order_by('link')
                    if jobs_for_that_company.count() > 1:
                        for job in jobs_for_that_company:
                            if job.link == "":
                                job.delete()
                         
                else:

                    if job.slug != new_slug:
                        job.slug = new_slug
                        job.save()
                    else:
                        print(f"Slug for {job.role.title} at {job.company.name} is already up to date.")