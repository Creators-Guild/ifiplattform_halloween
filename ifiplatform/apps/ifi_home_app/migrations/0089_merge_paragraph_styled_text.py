# Migration gotchas for this app: docs/claude_context/migrations.md
"""Data migration for merging the 'paragraph'/'styled_text' block pair
(top-level body, and 'text'/'styled_text' inside multi_column columns)
into one 'paragraph' block everywhere, following the schema change in
0088_alter_articlepage_body.

ArticlePage.body is read/written via raw SQL rather than the ORM here --
deliberately, not just for style. Wagtail's StreamBlock.to_python() (see
wagtail/blocks/stream_block.py) *silently drops* any top-level stream
child whose "type" isn't a currently-registered block on that StreamField,
the moment the field is loaded from the DB (`child_data["type"] in
self.child_blocks`). Once 0088 has renamed 'paragraph' to the merged
struct and removed 'styled_text' from the top-level block set, reading
`page.body` through the ORM -- even via a historical `apps.get_model`
instance depending on 0088 -- means every 'styled_text' block is *already
gone* by the time this migration's own code runs, before any rename can
apply. (Nested content, e.g. inside a multi_column column, isn't affected
by this since it's only resolved lazily on individual access -- confirmed
against a real copy of the dev DB, where the bug silently dropped every
top-level styled_text block but left column-level ones intact.) Raw SQL
sidesteps this entirely: it reads/writes the stored JSON as plain data,
never passing it through any StreamField's to_python.

wagtail.blocks.migrations (RenameStreamChildrenOperation etc.) is still
used for the actual raw-JSON transform -- that part only needs a
StreamField instance for its *structural* shape (which nesting level is a
StreamBlock/StructBlock/ListBlock), never for validating specific block
type names, so getting it from the current (post-0088) model is fine.
Block ids are preserved throughout (both operations spread
**child_block), so existing ArticleBlockStyle rows keep matching their
block after this runs.

Revision.content (page-history snapshots) doesn't have the to_python
silent-drop problem the live body does -- it's a plain JSONField holding a
raw dict, not itself a StreamField, so reading/writing revision.content
never goes through StreamField.to_python unless something explicitly
reconstructs a model instance from it (which this migration doesn't do);
ORM access is safe there. It has its own two gotchas instead though (wrong
content_type field, and its 'body' entry being a JSON *string* rather than
an already-parsed list) -- see _rewrite_revisions()'s own docstring.
"""

import json

from django.db import migrations

import wagtail.blocks.migrations.operations as ops
from wagtail.blocks.migrations.utils import apply_changes_to_raw_data

ARTICLE_TABLE = "ifi_home_app_articlepage"
COLUMN_PATH = "multi_column.columns.item.content"

TOP_LEVEL_OPS = [
    ("", ops.StreamChildrenToStructBlockOperation("paragraph", "paragraph")),
    ("paragraph", ops.RenameStructChildrenOperation("paragraph", "text")),
    ("", ops.RenameStreamChildrenOperation("styled_text", "paragraph")),
]
COLUMN_OPS = [
    (COLUMN_PATH, ops.StreamChildrenToStructBlockOperation("text", "paragraph")),
    (COLUMN_PATH, ops.RenameStreamChildrenOperation("styled_text", "paragraph")),
]


def _transform(raw_data, streamfield, op_list):
    for path, op in op_list:
        raw_data = apply_changes_to_raw_data(raw_data, path, op, streamfield)
    return raw_data


def _load(body):
    if not body:
        return []
    return json.loads(body) if isinstance(body, str) else body


def _rewrite_article_bodies(schema_editor, streamfield, op_list):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT page_ptr_id, body FROM {ARTICLE_TABLE}")
        rows = cursor.fetchall()

    for page_id, body in rows:
        raw = _load(body)
        if not raw:
            continue
        new_raw = _transform(raw, streamfield, op_list)
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {ARTICLE_TABLE} SET body = %s WHERE page_ptr_id = %s",
                [json.dumps(new_raw), page_id],
            )


def _rewrite_revisions(apps, streamfield, op_list):
    """Rewrites the 'body' snapshot inside every ArticlePage Revision's
    content dict. Two things here are easy to get wrong (both were wrong
    in the first version of this migration, caught afterwards -- see
    0090_fix_revision_content_type_and_body_shape.py, which repairs any
    database this buggy version already ran against):

    1. Revision.base_content_type is always the *base* class
       ("wagtailcore.page"), never the specific subclass -- filtering on
       it against ArticlePage's own ContentType matches nothing. The field
       that actually holds the specific subclass is plain content_type.

    2. Revision.content is a generic JSONField holding a dict of {field
       name: value}, but StreamField's own entry within that dict is
       serialized as a JSON *string* (matching how a StreamField's
       value_to_string() has always worked, independent of the live
       column's own native-JSON storage via use_json_field=True) -- not
       already-parsed list/dict the way the live ArticlePage.body column
       is. Needs an explicit json.loads()/json.dumps() round trip that
       the live-body path (_rewrite_article_bodies above) doesn't.
    """
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
        content["body"] = json.dumps(_transform(raw, streamfield, op_list))
        revision.content = content
        revision.save(update_fields=["content"])


def merge_forward(apps, schema_editor):
    ArticlePage = apps.get_model("ifi_home_app", "ArticlePage")
    streamfield = ArticlePage.body
    op_list = TOP_LEVEL_OPS + COLUMN_OPS
    _rewrite_article_bodies(schema_editor, streamfield, op_list)
    _rewrite_revisions(apps, streamfield, op_list)


def merge_backward(apps, schema_editor):
    # Reversing fully (recovering the original bare-string 'paragraph'
    # blocks) isn't possible -- StreamChildrenToStructBlockOperation isn't
    # reversible and we can no longer tell which 'paragraph' blocks used to
    # be bare paragraphs vs. styled_text. Renaming everything back to
    # 'styled_text' at least keeps the data loadable under the pre-0088
    # block definitions (both branches accepted a {"text": ...} struct).
    ArticlePage = apps.get_model("ifi_home_app", "ArticlePage")
    streamfield = ArticlePage.body
    op_list = [
        ("", ops.RenameStreamChildrenOperation("paragraph", "styled_text")),
        (COLUMN_PATH, ops.RenameStreamChildrenOperation("paragraph", "styled_text")),
    ]
    _rewrite_article_bodies(schema_editor, streamfield, op_list)
    _rewrite_revisions(apps, streamfield, op_list)


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0088_alter_articlepage_body"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [
        migrations.RunPython(merge_forward, merge_backward),
    ]
