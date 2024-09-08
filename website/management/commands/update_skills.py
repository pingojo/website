from django.core.management.base import BaseCommand
from django.db.models import Q

from website.models import Job, Skill


class Command(BaseCommand):
    help = 'Updates jobs by adding skills mentioned in their descriptions.'

    def handle(self, *args, **kwargs):
        # Fetch all jobs and skills once to avoid repeated DB hits
        jobs = Job.objects.prefetch_related('skills').all()
        skills = Skill.objects.all()

        jobs_updated = 0
        skill_job_map = {}  # To track job-skill additions

        # # Clear skills from all jobs in bulk
        # for job in jobs:
        #     job.skills.clear()

        for skill in skills:
            skill_name_lower = skill.name.lower()  # Convert skill name to lowercase

            # Create a query for jobs that contain the skill in their description
            matching_jobs = jobs.filter(
                description_markdown__icontains=f" {skill_name_lower} "
            )

            # Add the skill to each matching job
            for job in matching_jobs:
                if not job.skills.filter(id=skill.id).exists():  # Check if the skill is already added
                    job.skills.add(skill)
                    jobs_updated += 1
                    skill_job_map[job.title] = skill.name

        # Output aggregated results instead of per-update messages
        for job_title, skill_name in skill_job_map.items():
            self.stdout.write(self.style.SUCCESS(f'Added skill "{skill_name}" to job "{job_title}".'))

        self.stdout.write(self.style.SUCCESS(f'Finished updating jobs. Total jobs updated: {jobs_updated}'))
