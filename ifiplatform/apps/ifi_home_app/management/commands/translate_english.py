"""Translates pages and snippets waiting for English with DeepL. Run every
minute by ifiplatform-translate.timer; `--nightly` (its own timer) also
catches up on anything missing and cleans up old rows. See
docs/claude_context/translation_overlay.md."""

from django.core.management.base import BaseCommand

from ...translation import auto_translate


class Command(BaseCommand):
    help = (
        "Translates pages/snippets waiting for English with DeepL. --nightly: "
        "also marks everything with missing English, then cleans up old rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--nightly",
            action="store_true",
            help="Catch up on all missing English, then clean up.",
        )

    def handle(self, *args, **options):
        if options["nightly"]:
            summary = auto_translate.nightly()
            self.stdout.write(
                ", ".join(f"{key}: {value}" for key, value in summary.items())
            )
            return
        translated, failed = auto_translate.translate_waiting()
        if translated or failed:  # quiet when there was nothing to do
            self.stdout.write(f"Translated {translated}, failed {failed}.")
