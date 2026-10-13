"""Data step for 0147's schema change (UnionPage.sitting_members's "member"
block: description RichTextBlock -> responsibilities ListBlock(CharBlock())).

sitting_members is read/written via raw SQL rather than the ORM here, same
reasoning as 0089_merge_paragraph_styled_text.py: by the time this migration
runs, 0147 has already removed "description" from the "member" StructBlock's
own field list, so StructBlock.to_python() (which only reads fields it still
knows about) would silently make any existing description value unreachable
if read through a historical apps.get_model() instance -- raw SQL sidesteps
that entirely by treating the stored JSON as plain data.

sitting_members is stored as a JSON *string* here (confirmed against a real
copy of the dev DB: psycopg2 did not auto-parse it, unlike some other
JSONB columns elsewhere), so this always needs an explicit json.loads()/
json.dumps() round trip -- no defensive isinstance check needed the way
0089's _load() has, but kept anyway for safety in case that ever changes.

No Revision.content handling (unlike 0089) -- reverting a UnionPage to an
old revision is a much rarer path than live article editing/autosave, and
the worst case if it ever happens is that revision's responsibilities show
empty (the old description key is just ignored), not a crash. Deliberately
out of scope here.
"""

import json
import re
import uuid

from django.db import migrations
from django.utils.html import strip_tags

UNION_TABLE = "ifi_home_app_unionpage"


def _load(raw):
    if not raw:
        return []
    return json.loads(raw) if isinstance(raw, str) else raw


def _plain_text(description_html):
    # </p>, </div>, <br> etc. would otherwise run separate paragraphs
    # together with no space once tags are stripped.
    spaced = re.sub(r"</(p|div|li)>|<br\s*/?>", " ", description_html)
    return re.sub(r"\s+", " ", strip_tags(spaced)).strip()


def migrate_forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT page_ptr_id, sitting_members FROM {UNION_TABLE}")
        rows = cursor.fetchall()

    for page_id, raw in rows:
        stream = _load(raw)
        if not stream:
            continue

        changed = False
        for child in stream:
            if child.get("type") != "member":
                continue
            description = child.get("value", {}).get("description")
            if not description:
                continue
            text = _plain_text(description)
            if not text:
                continue
            child["value"]["responsibilities"] = [
                {"type": "item", "value": text, "id": str(uuid.uuid4())}
            ]
            changed = True

        if changed:
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {UNION_TABLE} SET sitting_members = %s WHERE page_ptr_id = %s",
                    [json.dumps(stream), page_id],
                )


def migrate_backward(apps, schema_editor):
    # Not reversible -- there's no way to reconstruct the original richtext
    # description from a plain-text responsibilities list, and the old
    # description value (still sitting unused in the stored JSON, see
    # 0147/article_unions.md) is what a real revert would need anyway.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0147_alter_articlestyle_intro_alignment_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
