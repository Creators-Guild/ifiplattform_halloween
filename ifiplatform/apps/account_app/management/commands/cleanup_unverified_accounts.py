"""Deletes signups that never confirmed their email address (is_active
stays False until verify_email_view flips it -- see account_app.views.
login_views) once they're older than settings.UNVERIFIED_ACCOUNT_RETENTION_
DAYS -- GDPR storage-limitation (Art. 5(1)(e)): there's no reason to keep a
name/email on file for an account nobody ever actually claimed.

An unverified account can never have authored an article, own a deck, or
hold editor permissions (all require being logged in, which requires
is_active), so unlike account_app.views.account_views.delete_account_view
this needs no attribution/ownership handling -- a plain delete is enough.

No task scheduler exists in this project (no Celery/django-crontab) -- this
is meant to be invoked periodically from outside Django entirely (host cron,
or a platform's own scheduled-job feature), not something wired up here.

Safe to re-run: matching accounts are simply gone after the first run, so a
second run just finds nothing left to delete.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Deletes unverified signups (is_active=False) older than "
        "settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS. Safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List matching accounts without deleting them.",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timezone.timedelta(
            days=settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS
        )
        queryset = get_user_model().objects.filter(
            is_active=False, date_joined__lt=cutoff
        )

        if options["dry_run"]:
            for user in queryset:
                self.stdout.write(f"  would delete: {user.username} ({user.email})")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run: {queryset.count()} unverified account(s) older than "
                    f"{settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS} days would be deleted."
                )
            )
            return

        # queryset.delete()'s own return value counts every cascaded row
        # (e.g. each User's Profile too), not just the accounts themselves --
        # count those separately first for an accurate message.
        account_count = queryset.count()
        queryset.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {account_count} unverified account(s) older than "
                f"{settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS} days."
            )
        )
