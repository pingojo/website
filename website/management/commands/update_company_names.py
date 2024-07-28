from django.core.management.base import BaseCommand
from django.db.models import F
from website.models import Company

class Command(BaseCommand):
    help = 'Updates Company objects where the name has double quotes in the beginning and end of the name'

    def handle(self, *args, **options):
        companies = Company.objects.filter(name__regex=r'^".*"$')

        for company in companies:
            new_name = company.name[1:-1]  # Remove the quotes at the beginning and the end
            
            print(f"Updating {company.name} to {new_name}")
            company.name = new_name
            company.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated company names'))
