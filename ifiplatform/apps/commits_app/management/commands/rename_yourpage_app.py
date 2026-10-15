"""Moves a database made while this app was called yourpage_app over to
commits_app: renames its tables, its django_migrations rows and its content
types (permissions and admin history hang off those, so they follow). Must
run before `migrate`, or migrate would create new, empty commits_app tables
next to the old ones. The deploy scripts run it every time; with nothing
left to rename it does nothing. Remove it, and its deploy lines, once every
database (server and local) has been moved."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

OLD = "yourpage_app"
NEW = "commits_app"


class Command(BaseCommand):
    help = "Renames the old yourpage_app tables and records to commits_app."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
        old_tables = [t for t in tables if t.startswith(f"{OLD}_")]
        if not old_tables:
            self.stdout.write("Nothing to rename.")
            return
        if any(t.startswith(f"{NEW}_") for t in tables):
            raise CommandError(
                f"Both {OLD}_* and {NEW}_* tables exist, so migrate already ran "
                f"before this command. Drop the {NEW}_* tables (they are new and "
                f"empty) and their rows in django_migrations, then run this again."
            )

        quote = connection.ops.quote_name
        with transaction.atomic(), connection.cursor() as cursor:
            for old in old_tables:
                new = NEW + old[len(OLD) :]
                cursor.execute(f"ALTER TABLE {quote(old)} RENAME TO {quote(new)}")
            cursor.execute(
                "UPDATE django_migrations SET app = %s WHERE app = %s", [NEW, OLD]
            )
            cursor.execute(
                "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
                [NEW, OLD],
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Renamed {len(old_tables)} table(s) from {OLD} to {NEW}."
            )
        )
