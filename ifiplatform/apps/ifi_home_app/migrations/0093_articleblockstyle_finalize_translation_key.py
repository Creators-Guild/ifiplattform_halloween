# Migration gotchas for this app: docs/claude_context/migrations.md
"""Schema step 3 of 3 for re-keying ArticleBlockStyle by translation_key
(see 0091's docstring for the full why) -- now that every row has one
(backfilled by 0092), makes translation_key required and drops the old
`article` FK entirely, swapping the unique constraint from
(article, block_id) to (translation_key, block_id).

Hand-written rather than `makemigrations`-generated: the autodetector
can't know translation_key is already fully backfilled at this point
(it only sees a model diff, not data), so it stops to interactively ask
for a one-off default -- not applicable here since every row already has
a real value from 0092.

Forward-only in practice: reversing this migration on SQLite (via Django's
auto-generated reverse for RemoveField, which rebuilds the table) re-adds
`article` as an empty column with no way to repopulate its old values --
there was never any code to restore an FK from translation_key, since the
whole point of this migration was to stop needing that FK at all. Chained
with 0092's own dedup step also not being reversible (rows it deleted are
just gone), attempting `migrate ifi_home_app 0090` from here will fail
partway through with an IntegrityError once it reaches 0091's own reverse
(trying to make the now-empty `article` column NOT NULL again) --
confirmed by hitting this for real while verifying this migration, which
is how this paragraph came to be written. Recovery in that situation is
the same as anywhere else in this project's history of hard-to-reverse
migrations: restore from a pre-migration backup and reapply forward only,
don't try to fix the reverse path in place.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0092_backfill_articleblockstyle_translation_key"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="articleblockstyle",
            name="unique_article_block_style",
        ),
        migrations.RemoveField(
            model_name="articleblockstyle",
            name="article",
        ),
        migrations.AlterField(
            model_name="articleblockstyle",
            name="translation_key",
            field=models.UUIDField(),
        ),
        migrations.AddConstraint(
            model_name="articleblockstyle",
            constraint=models.UniqueConstraint(
                fields=["translation_key", "block_id"],
                name="unique_article_block_style",
            ),
        ),
    ]
