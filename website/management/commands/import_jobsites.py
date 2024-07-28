import csv
from django.core.management.base import BaseCommand
from website.models import Source

class Command(BaseCommand):
    help = 'Import CSV file into the Company model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, mode='r') as file:
            reader = csv.reader(file)

            # Skip the header row
            next(reader)

            for row in reader:
                name, website, focus = row
                Source.objects.create(name=name, website=website, focus=focus)

        self.stdout.write(self.style.SUCCESS('CSV data imported successfully'))
