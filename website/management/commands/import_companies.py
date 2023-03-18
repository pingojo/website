# import_companies.py
import csv
from django.core.management.base import BaseCommand
from website.models import Company
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Import companies from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        with open(options["csv_file"], "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                base_slug = slugify(row["name"])
                company, created = Company.objects.update_or_create(
                    slug=base_slug,
                    defaults={
                        'name': row['name'],
                        'twitter_url': row['twitter_url'],
                        'number_of_employees_min': int(row['number_of_employees_min']) if row['number_of_employees_min'] else None,
                        'number_of_employees_max': int(row['number_of_employees_max']) if row['number_of_employees_max'] else None,
                        'description': row['description'],
                        'website': row['website'],
                        'city': row['city'],
                        'state': row['state'],
                        'country': row['country'],
                        'ceo': row['ceo'],
                        'ceo_twitter': row['ceo_twitter'],
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Successfully imported company: {row['name']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated company: {row['name']}"))