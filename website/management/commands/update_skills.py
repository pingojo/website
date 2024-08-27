from django.core.management.base import BaseCommand

from website.models import Job, Skill


class Command(BaseCommand):
    help = 'Updates jobs by adding skills mentioned in their descriptions.'

    def handle(self, *args, **kwargs):
        # Iterate over all skills
        # remove all skills from all jobs
        for job in Job.objects.all():
            job.skills.clear()
            
        skills = Skill.objects.all()
        jobs_updated = 0

        for skill in skills:
            skill_name_lower = skill.name.lower()  # Convert skill name to lowercase for case-insensitive matching
            if skill_name_lower:

                # Iterate over all jobs
                for job in Job.objects.all():
                    # Check if the skill name is in the job description
                    if job.description_markdown:
                        if " " + skill_name_lower + " " in job.description_markdown.lower():
                            # If the job doesn't already have this skill, add it
                            if not job.skills.filter(id=skill.id).exists():
                                job.skills.add(skill)
                                jobs_updated += 1
                                self.stdout.write(self.style.SUCCESS(f'Added skill "{skill.name}" to job "{job.title}".'))

        self.stdout.write(self.style.SUCCESS(f'Finished updating jobs. Total jobs updated: {jobs_updated}'))
