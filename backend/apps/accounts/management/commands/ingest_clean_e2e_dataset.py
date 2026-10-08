"""
Django Management Command: ingest_clean_e2e_dataset
Authoritatively ingests the 13 exported CSV files into PostgreSQL.

Usage:
    python manage.py ingest_clean_e2e_dataset [--dir PATH_TO_CSV_DIR] [--dry-run]
"""
import os
import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ingests all 13 CSV export files from clean_e2e_dataset into Namma Clinic database."

    def add_arguments(self, parser):
        default_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'exports', 'clean_e2e_dataset')
        )
        parser.add_argument(
            '--dir',
            default=default_dir,
            help="Directory path containing the 13 CSV export files."
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Perform validation without writing changes to the database."
        )

    def handle(self, *args, **options):
        # Add scripts directory to path to import ingestion engine
        scripts_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'scripts')
        )
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from ingest_clean_e2e_dataset import ingest_all

        csv_dir = options.get('dir')
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.NOTICE(f"Starting ingestion from: {csv_dir}"))
        ingest_all(source_dir=csv_dir, dry_run=dry_run)
        self.stdout.write(self.style.SUCCESS("CSV Ingestion finished successfully!"))
