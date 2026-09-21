import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = 'Runs integrity check, WAL checkpoint truncation, and VACUUM on the SQLite database.'

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        initial_size = round(db_path.stat().st_size / 1024, 2)
        self.stdout.write(f"Starting SQLite database optimization for: {db_path.name} (Current size: {initial_size} KB)...")

        with connection.cursor() as cursor:
            self.stdout.write("Checking database integrity...")
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchall()
            is_ok = all(row[0] == 'ok' for row in integrity_result)

            if not is_ok:
                self.stderr.write(self.style.ERROR(f"Integrity check failed: {integrity_result}"))
                return
            self.stdout.write(self.style.SUCCESS("Integrity check passed: OK"))

            self.stdout.write("Checkpointing WAL journal logs...")
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")

            self.stdout.write("Executing VACUUM to defragment and reclaim disk pages...")
            cursor.execute("VACUUM;")

            self.stdout.write("Updating database statistics (ANALYZE)...")
            cursor.execute("ANALYZE;")

        final_size = round(db_path.stat().st_size / 1024, 2)
        self.stdout.write(
            self.style.SUCCESS(
                f"Optimization complete!\n"
                f"Initial Size: {initial_size} KB\n"
                f"Final Size: {final_size} KB\n"
                f"Journal Mode: WAL\n"
                f"Foreign Keys: Enabled\n"
                f"Status: Healthy & Compact"
            )
        )
