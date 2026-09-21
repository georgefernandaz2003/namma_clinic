import os
import sqlite3
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Safely creates an online, point-in-time backup of the SQLite database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to store the backup file (defaults to backend/backups/)'
        )

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        if not db_path.exists():
            self.stderr.write(self.style.ERROR(f"Database file not found at: {db_path}"))
            return

        out_dir = Path(options['output_dir']) if options['output_dir'] else settings.BASE_DIR / 'backups'
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = out_dir / f"db_backup_{timestamp}.sqlite3"

        self.stdout.write(f"Initiating online SQLite hot-backup from {db_path.name}...")

        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(backup_file))

        with dst:
            src.backup(dst, pages=100)

        src.close()
        dst.close()

        file_size_kb = round(backup_file.stat().st_size / 1024, 2)
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup completed successfully!\n"
                f"File: {backup_file}\n"
                f"Size: {file_size_kb} KB"
            )
        )
