"""One-off fix for pages that drifted out of sync before ifi_home_app.
wagtail_hooks.sync_synchronized_fields_to_translations existed: re-syncs
wagtail-localize SynchronizedFields (status, and any other
plain non-text field wagtail-localize auto-classifies as synchronized) from
every nb page to its existing English translation. That hook only fires on
future publishes -- this command catches up everything published before it
was added (e.g. the Student Unions show_in_menu drift that prompted this -- that
field has since been replaced by menu groups, see models/menus.py).

Safe to re-run: re-syncing an already-synced page is a no-op.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from wagtail.models import Locale
from wagtail_localize.models import TranslationSource

from ifiplatform.apps.ifi_home_app.translation.sync import sync_synchronized_fields


class Command(BaseCommand):
    help = (
        "Re-syncs wagtail-localize SynchronizedFields (status, "
        "etc.) from every nb page to its existing English translation. "
        "One-off catch-up for pages that drifted before the auto-sync hook "
        "(ifi_home_app/wagtail_hooks.py) existed; safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List translations that would be synced without changing anything.",
        )

    def handle(self, *args, **options):
        nb_locale = Locale.objects.get(language_code="nb")
        synced_count = 0

        for source in TranslationSource.objects.filter(locale=nb_locale):
            try:
                page = source.get_source_instance()
            except ObjectDoesNotExist:
                continue  # source page was deleted since the translation was created

            if options["dry_run"]:
                for translation in source.translations.filter(enabled=True):
                    self.stdout.write(
                        f"  would sync: {source.object_repr!r} -> {translation.target_locale}"
                    )
                continue

            synced_count += len(sync_synchronized_fields(page))

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run: no changes made."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Synced {synced_count} translation(s).")
            )
