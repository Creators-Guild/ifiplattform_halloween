"""Data migration: unwrap any existing 'box' StreamField blocks in
ArticlePage.body into their own content, spliced in place -- run before the
schema change (next migration) that removes the 'box' block type entirely
(see article_models.py: box styling moved to the on-page editor, as a
per-block/per-column option on ArticleBlockStyle, replacing the old
Wagtail-side box block). The box's own visual styling (background/border/
radius) isn't preserved -- editors can re-apply box styling to the
unwrapped blocks individually via editor mode if they want it back. Boxes
can't be nested (see _body_content_blocks()'s old docstring), so this only
ever needs to look one level deep."""

from django.db import migrations


def unwrap_box_blocks(apps, schema_editor):
    ArticlePage = apps.get_model("ifi_home_app", "ArticlePage")
    for page in ArticlePage.objects.all():
        raw = list(page.body.raw_data)
        if not any(item["type"] == "box" for item in raw):
            continue
        new_raw = []
        for item in raw:
            if item["type"] == "box":
                new_raw.extend(item["value"].get("content") or [])
            else:
                new_raw.append(item)
        page.body = new_raw
        page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0076_remove_articlepage_show_in_newsbar"),
    ]

    operations = [
        migrations.RunPython(unwrap_box_blocks, migrations.RunPython.noop),
    ]
