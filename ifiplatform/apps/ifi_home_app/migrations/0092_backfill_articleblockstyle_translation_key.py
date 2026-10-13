"""Data step 2 of 3 for re-keying ArticleBlockStyle by translation_key
instead of by a specific ArticlePage (see 0091's own docstring for the
full why). For every existing row, sets translation_key from its current
`article` FK, then deduplicates: if more than one row ends up sharing the
same (translation_key, block_id) -- i.e. both a nb-locale and an en-locale
page independently accumulated a style override for what's really the
same block -- keeps the nb-locale one and discards the rest, matching the
project's existing "nb is the source of truth" convention (see
ArticlePage.publish_target).

Verified against a real copy of the dev DB before being written: 36
existing rows, all belonging to nb-locale articles (zero en-locale rows
exist at all -- this is the bug being fixed: en never got its own style
data in the first place), zero (translation_key, block_id) collisions.
The dedup step is still included for correctness on any other database
where an en-locale row might already exist independently.
"""

from django.db import migrations


def backfill_and_dedupe(apps, schema_editor):
    ArticleBlockStyle = apps.get_model("ifi_home_app", "ArticleBlockStyle")

    for style in ArticleBlockStyle.objects.select_related("article").all():
        if style.article_id is None:
            continue
        style.translation_key = style.article.translation_key
        style.save(update_fields=["translation_key"])

    groups = {}
    for style in ArticleBlockStyle.objects.select_related("article__locale").all():
        key = (style.translation_key, style.block_id)
        groups.setdefault(key, []).append(style)

    for key, rows in groups.items():
        if len(rows) <= 1:
            continue
        nb_rows = [
            r for r in rows if r.article and r.article.locale.language_code == "nb"
        ]
        keep = nb_rows[0] if nb_rows else rows[0]
        for row in rows:
            if row.pk != keep.pk:
                row.delete()


def clear_translation_key(apps, schema_editor):
    # Reverse of the backfill only -- the dedup (row deletion) above isn't
    # reversible, same as every other data-consolidating migration this
    # session. This just puts translation_key back to how 0091 left it
    # (all NULL) so a rollback lands on a valid, consistent schema state.
    ArticleBlockStyle = apps.get_model("ifi_home_app", "ArticleBlockStyle")
    ArticleBlockStyle.objects.update(translation_key=None)


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0091_articleblockstyle_translation_key_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_and_dedupe, clear_translation_key),
    ]
