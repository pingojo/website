from django.core.management.base import BaseCommand
from website.models import Job  # Change this to your actual app name and model
import html2text

class Command(BaseCommand):
    help = 'Converts Job descriptions from HTML to Markdown'

    def handle(self, *args, **options):
        # Get all Jobs
        jobs = Job.objects.all()

        # Initialize the HTML to Markdown converter
        converter = html2text.HTML2Text()
        converter.ignore_links = False

        for job in jobs:
            # Convert the HTML in the description to Markdown
            if job.description_markdown:
                markdown = converter.handle(job.description_markdown)

                # Update the job description with the Markdown
                job.description_markdown = markdown
                job.save()

        self.stdout.write(self.style.SUCCESS('Successfully converted job descriptions to Markdown.'))