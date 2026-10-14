"""Shows translated fields in English while English is active ("translate
on read") and keeps English out of the database (guard A).

Design rationale: docs/claude_context/translation_overlay.md"""

import logging
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from django.db import connections
from django.db.backends.signals import connection_created
from django.http import HttpResponsePermanentRedirect
from django.utils import translation

logger = logging.getLogger(__name__)

_english = ContextVar("english_active", default=False)
_raw = ContextVar("raw_norwegian", default=False)
MEMO_ATTR = "_english_values"


def english_active():
    """True while English is being displayed (GET/HEAD under /en/, English
    previews) and not in raw mode. Never in the admin, POST/AJAX, commands
    or the worker."""
    return _english.get() and not _raw.get()


@contextmanager
def english():
    """Turns English on for the block. Used by the display middleware and
    the English preview mode."""
    token = _english.set(True)
    try:
        yield
    finally:
        _english.reset(token)


@contextmanager
def raw_norwegian():
    """Translated fields give their stored Norwegian values in the block."""
    token = _raw.set(True)
    try:
        yield
    finally:
        _raw.reset(token)


class TranslatedField:
    """Replaces one field's attribute on its model. A data descriptor (get +
    set), so it runs on every read even after Django put the value in
    obj.__dict__; it wraps the original attribute (Django's, or Wagtail's
    StreamField Creator), which keeps holding the Norwegian value."""

    def __init__(self, original, field):
        self.original = original
        self.field = field

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = self.original.__get__(obj, cls)
        if not english_active():
            return value
        memo = obj.__dict__.setdefault(MEMO_ATTR, {})
        if self.field.name not in memo:
            memo[self.field.name] = _english_value(obj, self.field.name, value)
        return memo[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__.pop(MEMO_ATTR, None)
        if hasattr(self.original, "__set__"):
            self.original.__set__(obj, value)
        else:
            obj.__dict__[self.field.attname] = value


def _english_value(page, name, norwegian):
    from . import page_segments, stored_translations

    with raw_norwegian():
        try:
            translations = stored_translations.english_by_segment(page)
            if not translations:
                return norwegian
            return page_segments.apply_translations(page, name, translations)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Showing Norwegian %s.%s (pk %s): English couldn't be applied",
                type(page).__name__,
                name,
                page.pk,
            )
            return norwegian


class EnglishWriteBlocked(Exception):
    """Something tried to save a translated model while English was shown."""


_translated_tables = re.compile(r"(?!)")  # set by install()


def block_english_writes(execute, sql, params, many, context):
    """Database wrapper on every connection: while English is shown, INSERT
    and UPDATE on translated tables are refused, so English can't reach the
    database by any path (save, revisions, update(), bulk_update(), ...)."""
    if (
        english_active()
        and sql.lstrip()[:6].upper() in ("INSERT", "UPDATE")
        and _translated_tables.search(sql)
    ):
        raise EnglishWriteBlocked(
            "A translated page/snippet was about to be saved while English is "
            "shown, which would store English as Norwegian. Display code "
            f"must not save. Query: {sql[:120]}"
        )
    return execute(sql, params, many, context)


def _add_write_blocker(connection, **kwargs):
    if block_english_writes not in connection.execute_wrappers:
        connection.execute_wrappers.insert(0, block_english_writes)


# Django methods that copy a field's value back onto the object
# (setattr(obj, name, f(getattr(obj, name)))). Run in raw mode, so English
# never lands in the Norwegian slot: refresh_from_db also loads deferred
# fields; full_clean/clean_fields run inside every save().
_COPY_BACK_METHODS = ("refresh_from_db", "full_clean", "clean_fields")


def _keep_norwegian(method):
    def wrapper(self, *args, **kwargs):
        with raw_norwegian():
            return method(self, *args, **kwargs)

    wrapper.keeps_norwegian = True
    return wrapper


def install():
    """Installs translated fields on every model that has them (and Wagtail's
    own Page), plus the database guard. Called once from
    IfiHomeAppConfig.ready()."""
    global _translated_tables  # pylint: disable=global-statement
    from django.apps import apps
    from wagtail.models import Revision

    from .page_segments import check_translated_field, translated_field_names

    owners = {}
    for model in apps.get_models():
        for name in translated_field_names(model):
            check_translated_field(model, name)
            field = model._meta.get_field(name)
            owners.setdefault(field.model, set()).add(field)

    tables = {Revision._meta.db_table}
    for owner, fields in owners.items():
        for field in fields:
            original = owner.__dict__[field.attname]
            if not isinstance(original, TranslatedField):
                setattr(owner, field.attname, TranslatedField(original, field))
        for name in _COPY_BACK_METHODS:
            method = getattr(owner, name)
            if not getattr(method, "keeps_norwegian", False):
                setattr(owner, name, _keep_norwegian(method))
        tables.add(owner._meta.db_table)

    _translated_tables = re.compile(
        r"\b(?:" + "|".join(re.escape(table) for table in sorted(tables)) + r")\b"
    )
    connection_created.connect(_add_write_blocker, dispatch_uid="block_english_writes")
    for connection in connections.all(initialized_only=True):
        _add_write_blocker(connection)


@dataclass
class TranslationStatus:
    total: int
    deepl: int
    human: int
    missing: int
    errors: int


def translation_status(page):
    """How much of `page` has English, for nudges, dashboard, banner and the
    English editor. (translation/status.py's translation_status turns these
    counts into a nudge for one user.)"""
    from . import page_segments, stored_translations

    rows = stored_translations.lookup(page)
    status = TranslationStatus(0, 0, 0, 0, 0)
    for segment in page_segments.extract_segments(page):
        status.total += 1
        row = rows.get((segment.path, segment.norwegian_hash))
        if row is None:
            status.missing += 1
        elif row.has_error:
            status.errors += 1
        elif row.source == "human":
            status.human += 1
        else:
            status.deepl += 1
    return status


class EnglishPreviewMixin:
    """Adds an English preview next to the Norwegian one in Wagtail's
    preview panel. Previews never call DeepL."""

    @property
    def preview_modes(self):
        return [("", "Norsk"), ("en", "English")]

    def serve_preview(self, request, mode_name):
        if mode_name != "en":
            return super().serve_preview(request, mode_name)
        with english(), translation.override("en"):
            response = super().serve_preview(request, mode_name)
            if hasattr(response, "render"):
                response.render()  # templates render lazily, outside this block otherwise
            return response


_ADMIN_PATHS = ("/wagtail-admin/", "/admin/")


def shows_english(request):
    """English text is shown for GET/HEAD requests under /en/, outside the
    admin. POST/AJAX and the admin always see Norwegian."""
    return (
        request.method in ("GET", "HEAD")
        and translation.get_language() == "en"
        and not any(marker in request.path for marker in _ADMIN_PATHS)
    )


class EnglishDisplayMiddleware:
    """Turns English on while a page is shown under /en/ (must come after
    LocaleMiddleware, which picks the language from the address), loads
    English slugs at most once per request, and redirects a Norwegian slug
    under /en/ to the English address."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .english_urls import request_scope

        with request_scope():
            if shows_english(request):
                with english():
                    return self.get_response(request)
            return self.get_response(request)

    def process_exception(self, request, exception):
        from .english_urls import MovedToEnglishAddress

        if isinstance(exception, MovedToEnglishAddress):
            return HttpResponsePermanentRedirect(exception.url(request))
        return None
