"""DeepL in the background: marking objects as waiting for English (on
publish/save), translating what's waiting (`manage.py translate_english`,
every minute), the nightly catch-up, and filling in one object's missing
English. Parameters are called `page`, but snippets work too.

Design rationale: docs/claude_context/translation_overlay.md"""

import logging
import time
from datetime import timedelta

from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone
from wagtail.models import Page
from wagtail.signals import page_published

from ..models.translation import TranslationSettings, WaitingForEnglish
from . import deepl, english_urls, page_segments, stored_translations

logger = logging.getLogger(__name__)

# The banner stays hidden this long after an object starts waiting.
PENDING_MINUTES = 10
MAX_RETRY_WAIT_MINUTES = 60


def auto_translate_on():
    return TranslationSettings.load().auto_translate


def _mark_waiting(page, by_person=False):
    content_type_id, object_id = stored_translations.object_key(page)
    row, created = WaitingForEnglish.objects.get_or_create(
        content_type_id=content_type_id,
        object_id=object_id,
        defaults={"requested_at": timezone.now(), "requested_by_person": by_person},
    )
    if not created:
        row.requested_at = timezone.now()
        row.attempts, row.last_attempt_at, row.last_error = 0, None, ""
        row.requested_by_person = row.requested_by_person or by_person
        row.save()


def request_english(page):
    """Marks `page` as waiting for English; picked up within a minute. Does
    nothing without a DeepL key or with auto-translate off."""
    if deepl.is_configured() and auto_translate_on():
        _mark_waiting(page)


def request_subtree(page):
    """A person asked for English for `page` and every live page under it:
    marks them all waiting (translated by the every-minute run, even with
    automatic translation off). Returns the number of pages marked."""
    pages = [page] + list(page.get_descendants().live().specific())
    for each in pages:
        _mark_waiting(each, by_person=True)
    return len(pages)


def is_waiting(page):
    """True if `page` started waiting for English less than PENDING_MINUTES
    ago (the "not translated yet" banner stays hidden meanwhile)."""
    content_type_id, object_id = stored_translations.object_key(page)
    return WaitingForEnglish.objects.filter(
        content_type_id=content_type_id,
        object_id=object_id,
        requested_at__gte=timezone.now() - timedelta(minutes=PENDING_MINUTES),
    ).exists()


def fill_missing(page):
    """Translates `page`'s pieces without usable English with DeepL and
    stores the result (output that can't be put back is stored as an error
    and retried later). A page also gets its English slug from its first
    English title. Returns the number of pieces sent; raises on DeepL
    errors."""
    return fill_missing_many([page])


def fill_missing_many(objects):
    """fill_missing() for several objects at once, in as few DeepL requests
    as possible (all their missing pieces together, 50 per request): e.g. a
    menu's groups and links."""
    plan = []
    for obj in objects:
        stored_translations.drop_failed_machine_rows(obj)
        missing = stored_translations.missing_segments(obj)
        if missing:
            plan.append((obj, missing))
    texts = [segment.norwegian_text for _, missing in plan for segment in missing]
    english = iter(deepl.translate_texts(texts) if texts else [])
    for obj, missing in plan:
        good, failed = {}, {}
        for segment in missing:
            text = next(english)
            try:
                page_segments.check_english(segment, text)
                good[segment] = text
            except ValueError as error:
                failed[segment] = (text, str(error))
        stored_translations.save_machine(obj, good, failed)
    for obj in objects:
        if isinstance(obj, Page):
            _set_slug_from_title(obj)
    return len(texts)


def _set_slug_from_title(page):
    title = page_segments.extract_segments(page, "title")
    english = (
        stored_translations.english_by_segment(page).get(title[0]) if title else None
    )
    if english:
        english_urls.set_english_slug_if_missing(
            page, page_segments.plain_text(english)
        )


def _retry_wait(attempts):
    return timedelta(minutes=min(2**attempts, MAX_RETRY_WAIT_MINUTES))


def _waiting_object(row):
    """The live page or the snippet a row waits for, or None if it's gone
    (or unpublished: it's marked again when published)."""
    model = row.content_type.model_class()
    page = model._default_manager.filter(pk=row.object_id).first() if model else None
    if isinstance(page, Page) and not page.live:
        return None
    return page


def translate_waiting():
    """Translates everything waiting whose retry wait is over, oldest first,
    one object at a time (a row being translated is locked, so overlapping
    runs skip it). With automatic translation off, only what a person asked
    for. Returns (translated, failed) object counts."""
    translated = failed = 0
    if not deepl.is_configured():
        return translated, failed
    waiting = WaitingForEnglish.objects.order_by("requested_at")
    if not auto_translate_on():
        waiting = waiting.filter(requested_by_person=True)
    ids = waiting.values_list("pk", flat=True)
    for row_id in list(ids):
        with transaction.atomic():
            row = (
                WaitingForEnglish.objects.select_for_update(skip_locked=True)
                .filter(pk=row_id)
                .first()
            )
            now = timezone.now()
            if row is None or (
                row.last_attempt_at
                and now < row.last_attempt_at + _retry_wait(row.attempts)
            ):
                continue
            page = _waiting_object(row)
            if page is None:
                row.delete()
                continue
            try:
                with transaction.atomic():
                    fill_missing(page)
            except Exception as error:  # pylint: disable=broad-except
                logger.warning("DeepL failed for %s: %s", row.content_type, error)
                row.attempts += 1
                row.last_attempt_at = now
                row.last_error = f"{type(error).__name__}: {error}"[:2000]
                row.save()
                failed += 1
            else:
                row.delete()
                translated += 1
        time.sleep(deepl.DEEPL_CALL_DELAY_SECONDS)
    return translated, failed


def _translated_objects():
    """Every live page and every translated snippet."""
    yield from Page.objects.live().filter(depth__gt=1).specific()
    for model in apps.get_models():
        if not issubclass(model, Page) and page_segments.translated_field_names(model):
            yield from model._default_manager.all()


def nightly():
    """Nightly catch-up. With auto-translate on: redo DeepL rows a newer
    glossary affects, mark everything with missing or failed English as
    waiting, translate it. Always: cleanup. Returns a summary dict."""
    from ..models import GlossarySyncState
    from .english_overlay import translation_status
    from .glossary_terms import GLOSSARY_TERMS

    summary = {}
    if deepl.is_configured() and auto_translate_on():
        summary["stale glossary rows"] = stored_translations.forget_stale_glossary_rows(
            GLOSSARY_TERMS, GlossarySyncState.last_synced_at()
        )
        marked = 0
        for page in _translated_objects():
            status = translation_status(page)
            if status.missing or status.errors:
                _mark_waiting(page)
                marked += 1
        summary["marked waiting"] = marked
        summary["translated"], summary["failed"] = translate_waiting()
    summary["rows cleaned up"] = stored_translations.cleanup()
    return summary


def _page_published(sender, instance, **kwargs):
    request_english(instance)


def _snippet_saved(sender, instance, raw=False, **kwargs):
    if not raw:
        request_english(instance)


def connect_signals():
    """Pages are marked when published (any route: editor, scheduled
    publishing, workflows, commands), never on draft saves; snippets when
    saved. Called from IfiHomeAppConfig.ready()."""
    page_published.connect(_page_published, dispatch_uid="english_on_publish")
    for model in apps.get_models():
        if not issubclass(model, Page) and page_segments.translated_field_names(model):
            post_save.connect(
                _snippet_saved,
                sender=model,
                dispatch_uid=f"english_on_save_{model._meta.label}",
            )
