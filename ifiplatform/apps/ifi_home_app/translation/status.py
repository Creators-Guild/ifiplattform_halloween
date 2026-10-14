"""Whether a page's English is missing or out of date -- what the visitor
banner ("not translated yet") and the editor-facing nudges run on. Built on
english_overlay.translation_status(); parameters are Norwegian pages.

Design rationale: docs/claude_context/translation_nudge.md"""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from wagtail.models import Page

from ..models.translation import WaitingForEnglish
from . import auto_translate, stored_translations
from .english_overlay import english_active, raw_norwegian
from .english_overlay import translation_status as piece_counts


def _missing_or_failed(page):
    with raw_norwegian():
        counts = piece_counts(page)
    return counts.missing + counts.errors


def page_needs_translation(page):
    """The visitor banner's one rule: while English is shown, some English
    is missing or failed, and the page isn't waiting for DeepL (less than
    auto_translate.PENDING_MINUTES)."""
    if not english_active() or page.pk is None:
        return False
    return bool(_missing_or_failed(page)) and not auto_translate.is_waiting(page)


def translation_status(page, user=None):
    """None if `page`'s English is complete or DeepL is on its way, else
    {"page", "reason" ("missing"/"outdated"), "editor_url", "machine_url"}.
    "outdated": the page had English, but some Norwegian changed since.
    machine_url is always None now: the English editor has the button."""
    if page.is_root() or auto_translate.is_waiting(page):
        return None
    if not _missing_or_failed(page):
        return None
    from .english_editor import editor_url  # admin code: not at model import time

    had_english = bool(stored_translations.lookup(page))
    return {
        "page": page,
        "reason": "outdated" if had_english else "missing",
        "editor_url": editor_url(page),
        "machine_url": None,
    }


def _is_page_type(content_type_id):
    model = ContentType.objects.get_for_id(content_type_id).model_class()
    return model is not None and issubclass(model, Page)


def pages_needing_translation(user=None, limit=25):
    """(total count, first `limit` statuses) for the dashboard: pages a
    person needs to look at -- waiting for DeepL longer than
    PENDING_MINUTES (DeepL failing), or with English that didn't fit.
    Doesn't scan every page (too slow for a dashboard)."""
    stuck_before = timezone.now() - timedelta(minutes=auto_translate.PENDING_MINUTES)
    keys = set(
        WaitingForEnglish.objects.filter(requested_at__lt=stuck_before).values_list(
            "content_type_id", "object_id"
        )
    )
    keys |= stored_translations.objects_with_errors()
    page_ids = {
        object_id
        for content_type_id, object_id in keys
        if _is_page_type(content_type_id)
    }
    pages = (
        Page.objects.filter(pk__in=page_ids).specific().order_by("-last_published_at")
    )
    statuses = [status for status in map(translation_status, pages) if status]
    return len(statuses), statuses[:limit]
