"""wagtail_localize keeps its own DB records of translatable segments,
extracted from a frozen TranslationSource.content_json snapshot, each tied
to a TranslationContext row with a *cached* field_path string (e.g.
"sitting_members.member.description") -- see TranslationContext.
get_field_path in wagtail_localize/models.py, which only recomputes that
cache when it's empty. Migration 0148 fixed the live UnionPage.
sitting_members content but never touched wagtail_localize's own snapshot/
segment tables, so any UnionPage that had real description content still
carries stale segments referencing the now-removed "description" field --
opening its Wagtail admin edit view crashes with a KeyError in
wagtail_localize/views/edit_translation.py's get_segment_location_info,
which resolves the cached path against the *current* live block
definition.

Fix: resync each UnionPage's TranslationSource so wagtail_localize
re-extracts segments from current content. Same pattern already
established in ifi_home_app/translation/sync.py and management/commands/
sync_translated_page_fields.py: TranslationSource.update_from_db()
re-serializes from the live DB row and calls refresh_segments()
internally, which deletes any segment whose path is no longer present and
recreates the rest -- exactly what's needed here.

Live imports (not apps.get_model) are deliberate, unlike a typical data
migration -- update_from_db() is real wagtail_localize business logic
(StreamField block introspection against the *current* block definitions,
segment extraction, etc.) that can't be meaningfully reimplemented against
a frozen historical model. Safe specifically because this migration only
runs after 0148 has already fixed the live content each source resyncs
from.

Scoped to only nb UnionPages that still have a leftover (non-empty)
"description" value on some member -- i.e. exactly the pages 0148 actually
rewrote -- rather than every UnionPage. This isn't just an optimization:
some *unrelated* UnionPages (seeded before this project's own "always give
every optional CharBlock an explicit '' rather than omitting it" convention
existed -- see seed_dev_data/unions.py's own comment) have a genuine `None`
value on role_nickname/availability_note, which crashes wagtail_localize's
segment extraction with an unrelated TypeError
("`string` must be either a `StringValue` or a `str`. Got `NoneType`") the
moment it's resynced -- a pre-existing data-quality issue, not something
this migration should touch or attempt to fix.
"""

from django.db import migrations


def _has_leftover_description(page):
    # page.sitting_members's own StreamValue.value gives each block's
    # *deserialized* StructValue, built via the *current* member block
    # definition's to_python() -- which no longer has "description" as a
    # registered field at all, so block.value.get("description") is always
    # None regardless of what's actually stored. raw_data is the raw JSON
    # list of block dicts, unaffected by the current block definition --
    # exactly what's needed to see a leftover key the current definition
    # itself no longer knows about.
    return any(
        item.get("type") == "member" and item.get("value", {}).get("description")
        for item in page.sitting_members.raw_data
    )


def resync(apps, schema_editor):
    from wagtail_localize.models import TranslationSource

    from ifi_home_app.models.article_models import UnionPage

    for page in UnionPage.objects.filter(locale__language_code="nb"):
        if not _has_leftover_description(page):
            continue
        source = TranslationSource.objects.get_for_instance_or_none(page)
        if source is not None:
            source.update_from_db()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0148_migrate_union_position_description_to_responsibilities"),
    ]

    operations = [
        migrations.RunPython(resync, noop_reverse),
    ]
