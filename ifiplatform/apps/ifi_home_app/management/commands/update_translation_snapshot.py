"""Rewrites translation/translated_fields.json from the current models.

Run it when the rename protection test asks you to: after adding a
translated field or block, or after removing one on purpose. See
docs/claude_context/translation_overlay.md."""

import json

from django.core.management.base import BaseCommand

from ...translation.page_segments import SNAPSHOT_PATH, current_places


class Command(BaseCommand):
    help = "Rewrites translation/translated_fields.json from the current models."

    def handle(self, *args, **options):
        SNAPSHOT_PATH.write_text(
            json.dumps(current_places(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.stdout.write(f"Wrote {SNAPSHOT_PATH}")
