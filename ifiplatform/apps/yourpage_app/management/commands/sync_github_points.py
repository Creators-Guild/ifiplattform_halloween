"""Copies the event issues and their credits from GitHub -- see
yourpage_app/github_sync.py. Run after every deploy by
deploy/docker/deploy.sh, and safe to run by hand any time."""

from django.core.management.base import BaseCommand, CommandError

from yourpage_app.github_sync import sync
from yourpage_app.models import EventIssue, SyncStatus


class Command(BaseCommand):
    help = "Copies the event issues and who solved them from GitHub."

    def handle(self, *args, **options):
        if not sync():
            raise CommandError(f"Sync failed: {SyncStatus.get().last_error}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {EventIssue.objects.count()} event issue(s) from GitHub."
            )
        )
