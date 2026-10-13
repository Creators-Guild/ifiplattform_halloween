"""Machine-translates and publishes one nb page subtree into English.

The real implementation behind translation/views.py's "Translate and
publish" button -- that view only validates the request and launches this
command as a detached background process (see machine_translate_subtree()
in translation/views.py and docs/claude_context/translation_views.md for
why: a real subtree is too slow for any request/response cycle, and a
gunicorn worker timeout used to kill it mid-translation).

Resumable by construction: apply_machine_translation() skips any segment
that already has a StringTranslation, and each page's DeepL call covers
that whole page's untranslated segments in one request -- so a page's
translation is all-or-nothing (either every segment for that page gets a
StringTranslation together, or none do, since translate() now raises
cleanly on a bad response instead of partially succeeding -- see
translation/deepl.py). Combined with this command's own per-page
transactions, re-running after a partial failure costs zero extra DeepL
calls for pages that already succeeded; it only retries what failed or was
never reached. That's the entire retry strategy -- no separate
retry/backoff logic on top of it."""

import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from wagtail.models import Locale, Page

from wagtail_localize.machine_translators import get_machine_translator
from wagtail_localize.models import StringTranslation
from wagtail_localize.operations import TranslationCreator
from wagtail_localize.views.edit_translation import apply_machine_translation

from ifiplatform.apps.ifi_home_app.models import GlossarySyncState
from ifiplatform.apps.ifi_home_app.translation.glossary_terms import GLOSSARY_TERMS

TARGET_LANGUAGE_CODE = "en"

# Gap between DeepL calls -- one page's worth of untranslated segments per
# call. Without this, a real subtree (164 pages the night this was added)
# fires DeepL requests back-to-back with no gap at all, which is what
# tripped DeepL's own rate limiting in the first place.
DEEPL_CALL_DELAY_SECONDS = 1


class Command(BaseCommand):
    help = (
        "Machine-translates and publishes page_id and all its descendants "
        "into English. Not meant to be run by hand -- launched by "
        "translation/views.py's machine_translate_subtree view as a "
        "background process."
    )

    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)
        parser.add_argument("user_id", type=int)
        parser.add_argument(
            "--page-only",
            action="store_true",
            help="Translate just page_id, not its descendants.",
        )

    def handle(self, *args, **options):
        page = Page.objects.get(pk=options["page_id"]).specific
        user = get_user_model().objects.get(pk=options["user_id"])
        target_locale = Locale.objects.get(language_code=TARGET_LANGUAGE_CODE)
        machine_translator = get_machine_translator()
        if machine_translator is None:
            raise CommandError("No machine translator is configured.")

        pages = [page] if options["page_only"] else [page, *page.get_descendants()]

        creator = TranslationCreator(user, [target_locale])
        for p in pages:
            creator.create_translations(p)

        total = len(creator.mappings)
        translated_count = 0
        failed_count = 0
        for i, (source, translations) in enumerate(creator.mappings.items(), start=1):
            source_instance = source.get_source_instance()
            self.stdout.write(f"  machine-translating {i}/{total}: {source_instance}")
            publish = source_instance.live

            try:
                with transaction.atomic():
                    for translation in translations:
                        _clear_stale_glossary_translations(translation)
                        apply_machine_translation(
                            translation.id, user, machine_translator
                        )
                        translation.save_target(user=user, publish=publish)
                translated_count += 1
            except Exception as exc:  # pylint: disable=broad-except
                # Deliberately broad: any single page's failure (DeepL
                # rate-limited, network hiccup, whatever) must not abort
                # the rest of the batch or roll back pages already done --
                # see this module's own docstring on why re-running later
                # is the recovery path, not a retry loop here.
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"    failed: {source_instance} -- {exc}")
                )

            if i < total:
                time.sleep(DEEPL_CALL_DELAY_SECONDS)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {translated_count} translated, {failed_count} failed, "
                f"out of {total} page(s)."
            )
        )


def _clear_stale_glossary_translations(translation):
    """Deletes machine translations of segments containing a glossary term
    that predate the glossary's last sync, so apply_machine_translation()
    redoes them with the current glossary. See
    docs/claude_context/translation_views.md."""
    synced_at = GlossarySyncState.last_synced_at()
    if synced_at is None or not GLOSSARY_TERMS:
        return

    lower_terms = [term.lower() for term in GLOSSARY_TERMS]
    affected = [
        (segment.string_id, segment.context_id)
        for segment in translation.source.stringsegment_set.select_related("string")
        if any(term in segment.string.data.lower() for term in lower_terms)
    ]
    if not affected:
        return

    pair_filter = Q()
    for string_id, context_id in affected:
        pair_filter |= Q(translation_of_id=string_id, context_id=context_id)

    StringTranslation.objects.filter(
        pair_filter,
        locale=translation.target_locale,
        translation_type=StringTranslation.TRANSLATION_TYPE_MACHINE,
        updated_at__lt=synced_at,
    ).delete()
