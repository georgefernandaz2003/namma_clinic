"""
Management command to idempotently seed the 7 operational roles,
57 permissions, and role-permission mappings into PostgreSQL.
"""
from django.core.management.base import BaseCommand
from apps.accounts.services import seed_roles_and_permissions


class Command(BaseCommand):
    help = "Seed or reconcile Namma Clinic role and permission catalogue idempotently."

    def handle(self, *args, **options):
        result = seed_roles_and_permissions()
        self.stdout.write(self.style.SUCCESS(result["summary"]))
