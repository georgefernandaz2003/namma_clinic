"""
Alias management command for reset_demo_data.
Delegates to reset_demo_data with required confirmation safety.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Seed/reset demo dataset with controlled 10-patient baseline (delegates to reset_demo_data)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-demo-reset',
            action='store_true',
            help='Required confirmation flag to execute demo reset.',
        )

    def handle(self, *args, **options):
        call_command('reset_demo_data', *args, **options)
