"""Compiles .po translation files to .mo, without needing the system
gettext tools (msgfmt) that Django's own compilemessages requires.

Why this exists: this repo's dev machines don't all have gettext installed,
and installing it needs admin rights. `polib` (already a dependency via
wagtail_localize) can read/write the same .mo format in pure Python, so
this is a drop-in substitute for `manage.py compilemessages` for local dev.
If you do have msgfmt available, `manage.py compilemessages` works exactly
the same and there's no need for this command.
"""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import polib


class Command(BaseCommand):
    help = (
        "Compiles .po files to .mo using polib, as a substitute for "
        "manage.py compilemessages on machines without gettext installed."
    )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR).resolve()

        locale_dirs = list(settings.LOCALE_PATHS)
        for app_config in apps.get_app_configs():
            app_path = Path(app_config.path).resolve()
            # only this project's own apps -- skip third-party packages
            # (wagtail, django.contrib.*, ...) installed under .venv
            if base_dir not in app_path.parents and app_path != base_dir:
                continue
            app_locale_dir = app_path / "locale"
            if app_locale_dir.is_dir():
                locale_dirs.append(app_locale_dir)

        po_files = sorted(
            {
                po_file
                for locale_dir in locale_dirs
                for po_file in Path(locale_dir).glob("*/LC_MESSAGES/*.po")
            }
        )

        if not po_files:
            raise CommandError(f"No .po files found under {locale_dirs}")

        for po_file in po_files:
            po = polib.pofile(str(po_file))
            mo_file = po_file.with_suffix(".mo")
            po.save_as_mofile(str(mo_file))
            self.stdout.write(
                f"  compiled {po_file} -> {mo_file.name} ({len(po)} entries)"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Done: compiled {len(po_files)} .po file(s).")
        )
