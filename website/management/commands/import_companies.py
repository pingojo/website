import csv
from django.core.management.base import BaseCommand
from website.models import Company, Skill
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Import companies from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        # django_skill, _ = Skill.objects.get_or_create(name="Django", slug="django")
        # python_skill, _ = Skill.objects.get_or_create(name="Python", slug="python")

        with open(options["csv_file"], "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                base_slug = slugify(row["name"])
                company, created = Company.objects.update_or_create(
                    slug=base_slug,
                    defaults={
                        'name': row.get('name', ''),
                        'twitter_url': row.get('twitter_url', ''),
                        'greenhouse_url': row.get('greenhouse_url', ''),
                        'lever_url': row.get('greenhouse_url', ''),
                        'number_of_employees_min': int(row['number_of_employees_min']) if row.get('number_of_employees_min') else None,
                        'number_of_employees_max': int(row['number_of_employees_max']) if row.get('number_of_employees_max') else None,
                        'description': row.get('description', ''),
                        'website': row.get('website', ''),
                        'city': row.get('city', ''),
                        'state': row.get('state', ''),
                        'country': row.get('country', ''),
                        'ceo': row.get('ceo', ''),
                        'ceo_twitter': row.get('ceo_twitter', ''),
                    }
                )

                #company.skills.add(django_skill, python_skill)

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Successfully imported company: {row['name']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated company: {row['name']}"))
