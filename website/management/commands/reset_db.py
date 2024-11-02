from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Wipes all tables in the database (use with caution!)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force the operation without confirmation',
        )

    def handle(self, *args, **options):
        if not options['force']:
            confirm = input('This will PERMANENTLY DELETE all data in the database. Are you sure? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        with connection.cursor() as cursor:
            engine = settings.DATABASES['default']['ENGINE']
            if 'postgresql' in engine:
                # Disable foreign key checks and drop all tables for PostgreSQL
                cursor.execute("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
                self.stdout.write(self.style.SUCCESS('Successfully wiped all tables from the PostgreSQL database.'))
            elif 'mysql' in engine:
                # Disable foreign key checks and drop all tables for MySQL
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`;")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                self.stdout.write(self.style.SUCCESS('Successfully wiped all tables from the MySQL database.'))
            else:
                self.stdout.write(self.style.ERROR('This command only supports PostgreSQL and MySQL databases.'))