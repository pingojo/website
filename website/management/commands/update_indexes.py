from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Updates the search_vector field of all Job instances'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE website_job
                SET search_vector = 
                    setweight(to_tsvector('english', role.title), 'A') ||
                    setweight(to_tsvector('english', description_markdown), 'B') ||
                    setweight(to_tsvector('english', company.name), 'C')
                FROM website_role AS role, website_company AS company
                WHERE website_job.role_id = role.id AND website_job.company_id = company.id
            """)
        
        self.stdout.write(self.style.SUCCESS('Successfully updated search_vector field'))
