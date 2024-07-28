from django.core.management.base import BaseCommand
from website.models import Company

class Command(BaseCommand):
    help = 'Updates the website URLs of companies'

    def handle(self, *args, **options):
        companies = Company.objects.filter(website__startswith='http://')
        for company in companies:
            company.website = 'https://' + company.website[7:]
            company.save()
        self.stdout.write(self.style.SUCCESS('Website URLs updated successfully.'))
