"""Splits a field's Norwegian value into text pieces (Segment) and puts
English back. The only project file that imports wagtail-localize.

Parameters are called `page`, but menus, menu links and messages work too.

Design rationale: docs/claude_context/translation_overlay.md"""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from wagtail import blocks
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail_localize.segments import (
    OverridableSegmentValue,
    StringSegmentValue,
    TemplateSegmentValue,
)
from wagtail_localize.segments.extract import StreamFieldSegmentExtractor
from wagtail_localize.segments.ingest import StreamFieldSegmentsWriter
from wagtail_localize.strings import (
    StringValue,
    extract_strings,
    restore_strings,
    validate_translation_links,
)

# Same value as wagtail-localize's String.UUID_NAMESPACE, so English copied
# from its tables matches. Ours from here on: changing it orphans every row.
HASH_NAMESPACE = uuid.UUID("59ed7d1c-7eb5-45fa-9c8b-7a7057ed56d7")

# Wagtail's own Page fields that visitors see.
PAGE_FIELDS = ["title", "seo_title", "search_description"]

_BLOCK_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_TEXT_BLOCKS = (
    blocks.CharBlock,
    blocks.TextBlock,
    blocks.BlockQuoteBlock,
    blocks.RichTextBlock,
)
_KEPT_VALUES = (StringSegmentValue, TemplateSegmentValue, OverridableSegmentValue)


def segment_hash(norwegian_text):
    return uuid.uuid5(HASH_NAMESPACE, norwegian_text)


@dataclass(frozen=True)
class Segment:
    """One piece of Norwegian text at one place. `path` is e.g.
    "body.<block id>.text"; `norwegian_text` is in stored form (HTML-escaped,
    links as <a id="a1"> placeholders). A rich text field gives several
    pieces with the same path, so a piece is always path + text."""

    path: str
    norwegian_text: str

    @property
    def norwegian_hash(self):
        return segment_hash(self.norwegian_text)


def translated_field_names(model):
    """Every field of `model` shown in English: Wagtail's PAGE_FIELDS for
    pages, then the model's own `translated_fields`."""
    names = list(getattr(model, "translated_fields", ()))
    if issubclass(model, Page):
        names = PAGE_FIELDS + [name for name in names if name not in PAGE_FIELDS]
    return names


def check_translated_field(model, name):
    """Raises ImproperlyConfigured unless `model.name` is text for people."""
    field = model._meta.get_field(name)
    wrong_type = not isinstance(
        field, (StreamField, RichTextField, models.CharField, models.TextField)
    )
    technical = isinstance(
        field, (models.URLField, models.EmailField, models.SlugField)
    )
    if wrong_type or technical or getattr(field, "choices", None):
        raise ImproperlyConfigured(
            f"{model.__name__}.translated_fields lists '{name}', which isn't text "
            "for people (a choice, URL, email, slug or non-text field). Remove it."
        )


def place_of(path):
    """`path` with block ids replaced by *, e.g. "body.*.text"."""
    return _BLOCK_ID.sub("*", path)


def _is_excluded(model, path):
    return place_of(path) in getattr(model, "untranslated_block_paths", ())


def _stored_value(page, name):
    from .english_overlay import raw_norwegian

    with raw_norwegian():
        return getattr(page, name)


def _segment_values(model, field, value):
    """wagtail-localize segment values for one field's Norwegian `value`,
    paths starting with the field name, in order. Page and image choosers
    are left out: links and images stay Norwegian."""
    if isinstance(field, StreamField):
        values = StreamFieldSegmentExtractor(field).handle_stream_block(value)
    elif isinstance(field, RichTextField):
        # a RichText object until the field is saved and loaded again
        template, strings = extract_strings(getattr(value, "source", value) or "")
        values = [TemplateSegmentValue("", "html", template, len(strings))] + [
            StringSegmentValue("", string, attrs=attrs) for string, attrs in strings
        ]
    else:
        values = [StringSegmentValue("", value)] if value else []
    values = [
        value.wrap(field.name) for value in values if isinstance(value, _KEPT_VALUES)
    ]
    for order, value in enumerate(values):
        value.order = order
    return values


def extract_segments(page, field_name=None):
    """The Norwegian pieces of one field, or of every translated field when
    `field_name` is omitted. Always reads the stored Norwegian values."""
    model = type(page)
    names = [field_name] if field_name else translated_field_names(model)
    segments = []
    for name in names:
        field = model._meta.get_field(name)
        for value in _segment_values(model, field, _stored_value(page, name)):
            if (
                isinstance(value, StringSegmentValue)
                and not value.is_empty()  # e.g. an empty optional block field
                and not _is_excluded(model, value.path)
            ):
                segments.append(Segment(value.path, value.string.data))
    return list(dict.fromkeys(segments))


def apply_translations(page, field_name, translations):
    """The English value of one field: text, rich text HTML or a StreamValue.
    `translations` maps Segment -> English (stored form); pieces without
    English stay Norwegian. Built from a fresh copy, `page` is not changed."""
    model = type(page)
    field = model._meta.get_field(field_name)
    norwegian = _stored_value(page, field_name)
    values = []
    for value in _segment_values(model, field, norwegian):
        if isinstance(value, StringSegmentValue) and not _is_excluded(
            model, value.path
        ):
            english = translations.get(Segment(value.path, value.string.data))
            if english is not None:
                value = StringSegmentValue(
                    value.path,
                    StringValue(english),
                    attrs=value.attrs,
                    order=value.order,
                )
        values.append(value)

    if isinstance(field, StreamField):
        fresh = field.to_python(norwegian.get_prep_value())
        inner = [value.unwrap()[1] for value in values]
        return StreamFieldSegmentsWriter(field, None, None).handle_stream_block(
            fresh, inner
        )
    if isinstance(field, RichTextField):
        if not values:
            return norwegian
        strings = [(value.string, value.attrs) for value in values[1:]]
        return restore_strings(values[0].template, strings)
    return values[0].string.render_text() if values else norwegian


def stored_form(text):
    """Plain text in stored form (HTML-escaped, newlines as <br>)."""
    return StringValue.from_plaintext(text).data


def plain_text(stored_text):
    """Stored-form text as plain text (tags removed, entities unescaped)."""
    return StringValue(stored_text).render_text()


def check_english(segment, english):
    """Raises ValueError if `english` can't be put back in place of
    `segment` (disallowed HTML, or a link the Norwegian doesn't have)."""
    StringValue.from_translated_html(english)
    validate_translation_links(segment.norwegian_text, english)


def places(model):
    """Every translated place on `model`, for the rename protection test, as
    {readable: stored}: readable names block types and struct fields, e.g.
    "body → image → caption" ("[]" marks a list item); stored is the form
    stored paths take, block ids as *, e.g. "body.*.caption"."""
    found = {}
    excluded = getattr(model, "untranslated_block_paths", ())
    for name in translated_field_names(model):
        field = model._meta.get_field(name)
        if not isinstance(field, StreamField):
            found[name] = name
            continue
        for readable, stored in _block_places(field.stream_block):
            stored_path = ".".join((name,) + stored)
            if stored_path not in excluded:
                found[" → ".join((name,) + readable)] = stored_path
    return dict(sorted(found.items()))


def _block_places(block):
    """(readable, stored) path parts for every text block under `block`:
    readable names block types, stored has * where the stored path has a
    block or list item id."""
    if isinstance(block, _TEXT_BLOCKS):
        return [((), ())]
    if isinstance(block, blocks.StreamBlock):
        return [
            ((name,) + readable, ("*",) + stored)
            for name, child in block.child_blocks.items()
            for readable, stored in _block_places(child)
        ]
    if isinstance(block, blocks.StructBlock):
        return [
            ((name,) + readable, (name,) + stored)
            for name, child in block.child_blocks.items()
            for readable, stored in _block_places(child)
        ]
    if isinstance(block, blocks.ListBlock):
        return [
            (("[]",) + readable, ("*",) + stored)
            for readable, stored in _block_places(block.child_block)
        ]
    return []


SNAPSHOT_PATH = Path(__file__).with_name("translated_fields.json")


def current_places():
    """{"app_label.Model": places(model)} for every project model that has
    translated places: what translated_fields.json should contain."""
    from django.apps import apps
    from django.conf import settings

    project = str(settings.BASE_DIR)
    return {
        model._meta.label: places(model)
        for model in apps.get_models()
        if model._meta.app_config.path.startswith(project) and places(model)
    }
