"""The only code that reads or writes the SegmentTranslation table. Plain
functions; parameters are called `page`, but menus, menu links and
messages work too.

Design rationale: docs/claude_context/translation_overlay.md"""

from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from wagtail.models import Page

from ..models.translation import SegmentTranslation
from .page_segments import Segment, extract_segments

ROWS_ATTR = "_english_rows"


def object_key(page):
    """(content type id, object id). Pages use their specific type, so a
    plain Page and its .specific share rows."""
    if isinstance(page, Page):
        return page.content_type_id, page.pk
    return ContentType.objects.get_for_model(page).id, page.pk


def lookup(page):
    """All of `page`'s rows as {(segment_path, norwegian_hash): row}, in one
    query, remembered on the page object for the rest of the request."""
    rows = page.__dict__.get(ROWS_ATTR)
    if rows is None:
        if page.pk is None:
            rows = {}
        else:
            content_type_id, object_id = object_key(page)
            rows = {
                (row.segment_path, row.norwegian_hash): row
                for row in SegmentTranslation.objects.filter(
                    content_type_id=content_type_id, object_id=object_id
                )
            }
        page.__dict__[ROWS_ATTR] = rows
    return rows


def english_by_segment(page):
    """{Segment: English text} for every usable row of `page`."""
    return {
        Segment(row.segment_path, row.norwegian_text): row.english_text
        for row in lookup(page).values()
        if not row.has_error
    }


def _forget(page):
    page.__dict__.pop(ROWS_ATTR, None)


def save_human(page, segment, english, user):
    """A person's English for `segment` (the place + Norwegian text they were
    looking at). Always replaces what's there, DeepL or human."""
    content_type_id, object_id = object_key(page)
    SegmentTranslation.objects.update_or_create(
        content_type_id=content_type_id,
        object_id=object_id,
        segment_path=segment.path,
        norwegian_hash=segment.norwegian_hash,
        defaults={
            "norwegian_text": segment.norwegian_text,
            "english_text": english,
            "source": "human",
            "translated_by": user,
            "has_error": False,
            "error": "",
        },
    )
    _forget(page)


def save_machine(page, english_by_piece, failed=None):
    """DeepL's English, {Segment: English}; `failed` is {Segment: (English,
    error)} for output that can't be put back (stored with has_error, so it
    is shown as missing and retried). Insert-only, in one statement
    (INSERT ... ON CONFLICT DO NOTHING): fills places with no row yet and
    never touches an existing row, so a human fix always wins."""
    content_type_id, object_id = object_key(page)
    pieces = [(segment, english, "") for segment, english in english_by_piece.items()]
    pieces += [
        (segment, english, error)
        for segment, (english, error) in (failed or {}).items()
    ]
    SegmentTranslation.objects.bulk_create(
        [
            SegmentTranslation(
                content_type_id=content_type_id,
                object_id=object_id,
                segment_path=segment.path,
                norwegian_text=segment.norwegian_text,
                norwegian_hash=segment.norwegian_hash,
                english_text=english,
                source="deepl",
                has_error=bool(error),
                error=error,
            )
            for segment, english, error in pieces
        ],
        ignore_conflicts=True,
    )
    _forget(page)


def drop_failed_machine_rows(page):
    """Deletes `page`'s DeepL rows marked has_error, so they're retried."""
    content_type_id, object_id = object_key(page)
    SegmentTranslation.objects.filter(
        content_type_id=content_type_id,
        object_id=object_id,
        source="deepl",
        has_error=True,
    ).delete()
    _forget(page)


def forget_stale_glossary_rows(terms, synced_at):
    """Deletes DeepL rows containing a glossary term (case-insensitive, like
    DeepL's own matching) that predate the glossary's last sync, so they're
    redone with the current glossary. Returns the number deleted."""
    if not terms or synced_at is None:
        return 0
    lowered = [term.lower() for term in terms]
    stale = [
        pk
        for pk, text in SegmentTranslation.objects.filter(
            source="deepl", updated_at__lt=synced_at
        ).values_list("pk", "norwegian_text")
        if any(term in text.lower() for term in lowered)
    ]
    return SegmentTranslation.objects.filter(pk__in=stale).delete()[0]


def objects_with_errors():
    """{(content type id, object id)} of everything with English that
    couldn't be put back (has_error)."""
    return set(
        SegmentTranslation.objects.filter(has_error=True).values_list(
            "content_type_id", "object_id"
        )
    )


def missing_segments(page):
    """`page`'s pieces that have no English yet."""
    rows = lookup(page)
    return [
        segment
        for segment in extract_segments(page)
        if (segment.path, segment.norwegian_hash) not in rows
    ]


def _current_versions(page):
    """The versions whose pieces count as current: the stored object (the
    published version for live pages) and the latest draft, if any. Drafts
    keep rows alive, they never delete any."""
    versions = [page]
    if isinstance(page, Page) and page.has_unpublished_changes:
        draft = page.get_latest_revision_as_object()
        if draft is not None:
            versions.append(draft)
    return versions


def cleanup():
    """Deletes rows nobody can need any more:
    1. the page/snippet was deleted
    2. the place is no longer on the page (published or draft)
    3. old Norwegian at a place: old DeepL rows go; only the newest old
       human row is kept (a suggestion for the English editor).
    Returns the number of rows deleted."""
    deleted = 0
    by_object = defaultdict(list)
    for row in SegmentTranslation.objects.order_by("-updated_at"):
        by_object[(row.content_type_id, row.object_id)].append(row)

    for (content_type_id, object_id), rows in by_object.items():
        model = ContentType.objects.get_for_id(content_type_id).model_class()
        page = model._default_manager.filter(pk=object_id).first() if model else None
        if page is None:
            doomed = [row.pk for row in rows]
        else:
            current = set()
            for version in _current_versions(page):
                current.update(
                    (segment.path, segment.norwegian_hash)
                    for segment in extract_segments(version)
                )
            places = {path for path, _ in current}
            doomed, kept_old_human = [], set()
            for row in rows:  # newest first
                if row.segment_path not in places:
                    doomed.append(row.pk)
                elif (row.segment_path, row.norwegian_hash) in current:
                    continue
                elif row.source == "human" and row.segment_path not in kept_old_human:
                    kept_old_human.add(row.segment_path)
                else:
                    doomed.append(row.pk)
        if doomed:
            with transaction.atomic():
                deleted += SegmentTranslation.objects.filter(pk__in=doomed).delete()[0]
    return deleted


def rename_segment_path(apps, model_name, old, new):
    """For migrations that rename a translated field, or a field inside a
    block: moves the stored English from places matching `old` to `new`.
    Patterns use stored-path form, * for a block id, e.g.
        rename_segment_path(apps, "ArticlePage", "body.*.caption", "body.*.image_caption")
    A renamed field also moves everything under it ("body" -> "content").
    Renaming only a block type ("image" -> "picture") moves nothing: stored
    places use block ids, not type names."""
    old_parts, new_parts = old.split("."), new.split(".")
    if old_parts.count("*") != new_parts.count("*"):
        raise ValueError("`old` and `new` must have the same number of *")
    content_type = (
        apps.get_model("contenttypes", "ContentType")
        .objects.filter(app_label="ifi_home_app", model=model_name.lower())
        .first()
    )
    if content_type is None:
        return
    rows = apps.get_model("ifi_home_app", "SegmentTranslation").objects
    for row in rows.filter(content_type=content_type):
        parts = row.segment_path.split(".")
        head = parts[: len(old_parts)]
        if len(head) < len(old_parts) or any(
            want not in ("*", have) for want, have in zip(old_parts, head)
        ):
            continue
        ids = iter(have for want, have in zip(old_parts, head) if want == "*")
        moved = [next(ids) if part == "*" else part for part in new_parts]
        new_path = ".".join(moved + parts[len(old_parts) :])
        clash = rows.filter(
            content_type=content_type,
            object_id=row.object_id,
            segment_path=new_path,
            norwegian_hash=row.norwegian_hash,
        )
        if clash.exists():
            row.delete()
        else:
            row.segment_path = new_path
            row.save(update_fields=["segment_path"])
