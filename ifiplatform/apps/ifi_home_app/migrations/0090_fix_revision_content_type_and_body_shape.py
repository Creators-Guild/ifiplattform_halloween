# Migration gotchas for this app: docs/claude_context/migrations.md
"""Repairs the fallout from two bugs in 0089_merge_paragraph_styled_text's
_rewrite_revisions() (see that function's own updated docstring for the
full explanation): it filtered Revision by the wrong content-type field
(base_content_type, always "wagtailcore.page", never the specific
subclass), so it silently rewrote *zero* of the pre-existing ArticlePage
revisions -- every one of them was left holding the pre-merge body shape
(a bare RichText string for 'paragraph', or a 'styled_text'-typed block
StreamField's own current definition no longer recognises).

Two consequences, both real, discovered from a live user report ("if I
edit through wagtail... the text disappears"):

1. Wagtail's admin StreamField editor loads a page's *latest revision*
   into the form, not the live row directly. For any article with pre-
   0089 revision history (i.e. basically all of them), that revision
   still had the old shape -- so a 'paragraph' block's RichText widget
   received a bare string where it now expects {"text": ...}, rendering
   empty. Saving from that broken-looking form (autosave or Publish)
   wrote the empty state back, permanently losing the text.

2. Separately, actually *publishing* one of these stale revisions (either
   via the Wagtail admin, or via this project's own article_views.
   publish_page endpoint -- which publishes get_latest_revision()) pushes
   the old-shaped content back onto the live row, undoing 0089's fix for
   that page. A handful of pages already got hit exactly this way while
   testing the publish/unpublish feature this session.

Deliberately uses its own small idempotent walker (_fix_paragraph_shape)
rather than 0089's wagtail.blocks.migrations operations
(StreamChildrenToStructBlockOperation et al): those match purely on a
block's *type* ("paragraph"), not its current value shape, so blindly
re-running them here -- against data that's a priori an unknown mix of
already-fixed and still-broken blocks, on both the live-body and revision
side -- would double-wrap anything already correct ({"text": ...} ->
{"paragraph": {"text": ...}}). The walker below only touches a 'paragraph'
block whose value is still a bare string (or a leftover 'styled_text'/
'text' block, from a revision predating 0089 that a corrected 0089 or a
previous run of this migration hasn't reached yet), and is a plain no-op
on anything already shaped correctly -- safe to run on any database state,
including re-running this migration itself.

Verified against a real copy of the dev DB before being written: found
404 pre-existing revisions, all with content['body'] as a JSON *string*
(not an already-parsed list -- Revision.content serializes StreamField
fields as a string via value_to_string, independent of the live column's
own native-json storage), and 6 live ArticlePage rows already showing the
bare-string regression from (2). No block ids were found missing entirely
(the more serious to_python-silent-drop failure mode never actually fired
here, since every affected block's *type* was still 'paragraph' -- a
recognised type either way, just with the wrong value shape).
"""

import json

from django.db import migrations

ARTICLE_TABLE = "ifi_home_app_articlepage"


def _fix_paragraph_shape(blocks):
    """In place: wraps a still-bare-string 'paragraph' value as
    {"text": ...}, and renames any leftover 'styled_text'/'text' block to
    'paragraph' (wrapping its value too if it's still a bare string).
    Recurses into multi_column columns. No-ops on anything already in the
    correct shape."""
    if not isinstance(blocks, list):
        return
    for block in blocks:
        if not isinstance(block, dict) or "type" not in block:
            continue
        if block["type"] == "paragraph" and isinstance(block.get("value"), str):
            block["value"] = {"text": block["value"]}
        elif block["type"] in ("styled_text", "text"):
            block["type"] = "paragraph"
            if isinstance(block.get("value"), str):
                block["value"] = {"text": block["value"]}
        if block["type"] == "multi_column" and isinstance(block.get("value"), dict):
            for column in block["value"].get("columns") or []:
                column_value = column.get("value") if isinstance(column, dict) else None
                if isinstance(column_value, dict):
                    _fix_paragraph_shape(column_value.get("content"))


def _fix_live_bodies(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT page_ptr_id, body FROM {ARTICLE_TABLE}")
        rows = cursor.fetchall()

    for page_id, body in rows:
        if not body:
            continue
        raw = json.loads(body) if isinstance(body, str) else body
        if not raw:
            continue
        before = json.dumps(raw)
        _fix_paragraph_shape(raw)
        after = json.dumps(raw)
        if before == after:
            continue
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {ARTICLE_TABLE} SET body = %s WHERE page_ptr_id = %s",
                [after, page_id],
            )


def _fix_revisions(apps):
    Revision = apps.get_model("wagtailcore", "Revision")
    ContentType = apps.get_model("contenttypes", "ContentType")
    article_ct = ContentType.objects.filter(
        app_label="ifi_home_app", model="articlepage"
    ).first()
    if article_ct is None:
        return
    for revision in Revision.objects.filter(content_type=article_ct).iterator():
        content = revision.content
        if not isinstance(content, dict):
            continue
        body = content.get("body")
        if not body or not isinstance(body, str):
            continue
        raw = json.loads(body)
        if not raw:
            continue
        before = json.dumps(raw)
        _fix_paragraph_shape(raw)
        after = json.dumps(raw)
        if before == after:
            continue
        content["body"] = after
        revision.content = content
        revision.save(update_fields=["content"])


def fix_forward(apps, schema_editor):
    _fix_live_bodies(schema_editor)
    _fix_revisions(apps)


def fix_backward(apps, schema_editor):
    # Nothing to reverse -- this migration only repairs data that was
    # already supposed to be in the merged shape (0089's own intent), it
    # doesn't introduce a new shape of its own to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0089_merge_paragraph_styled_text"),
    ]

    operations = [
        migrations.RunPython(fix_forward, fix_backward),
    ]
