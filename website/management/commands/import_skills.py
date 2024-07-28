# management/commands/import_skills.py

from django.core.management.base import BaseCommand
from website.models import Skill


class Command(BaseCommand):
    help = 'Import a list of skills'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='The name of the file containing the skills')

    def handle(self, *args, **options):
        filename = options['filename']
        with open(filename) as f:
            skills = [line.strip() for line in f.readlines()]

        for skill_name in skills:
            skill, created = Skill.objects.get_or_create(name=skill_name, slug=skill_name.lower())
            if created:
                self.stdout.write(f'Successfully created skill: {skill}')
            else:
                self.stdout.write(f'Skill already exists: {skill}')
