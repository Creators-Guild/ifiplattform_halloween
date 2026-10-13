from django.db import migrations, models


class Migration(migrations.Migration):
    """Hand-written instead of autodetected: makemigrations' interactive
    rename-detection prompt doesn't fire from a piped/non-tty stdin in this
    environment, and would otherwise have generated a RemoveField+AddField
    (data loss) for content_font_size instead of a RenameField (data
    preserved) -- see project memory on this session's migration
    discipline. A straight rename here preserves every article's existing
    value; the multiplier reinterpretation of that value going forward is
    an accepted one-time tradeoff (see ArticleStyle.content_font_size_
    multiplier's own help_text), not a data-loss concern."""

    dependencies = [
        ("ifi_home_app", "0096_remove_articlepage_content_alignment_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="articlestyle",
            old_name="content_font_size",
            new_name="content_font_size_multiplier",
        ),
        migrations.AlterField(
            model_name="articlestyle",
            name="content_font_size_multiplier",
            field=models.FloatField(
                default=1,
                help_text=(
                    "Multiplies the effective font size of every heading/paragraph/"
                    "image-caption/column-title block in the body, on top of each "
                    "block's own font size (1 = no change) -- see "
                    "_effective_heading_style()'s display_font_size. Unlike "
                    "alignment above, this never overwrites any block's own stored "
                    "font_size -- it's a display-time scale, not a per-block "
                    "override. Title, intro and meta have their own separate font "
                    "size controls, unaffected by this."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="articlestyle",
            name="content_alignment",
            field=models.CharField(
                choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
                default="left",
                help_text=(
                    "Saving a change to this OVERWRITES the alignment of every "
                    "alignment-capable block in the article body (heading, "
                    "paragraph, image, image captions, column titles) -- see "
                    "save_quick_style's apply_alignment_to_blocks handling and "
                    "alignment_capable_block_ids(). A block can opt out via its own "
                    "'exclude_from_global_alignment' flag on ArticleBlockStyle. "
                    "Does not affect the title/intro/meta block above the body, "
                    "which has its own separate alignment controls."
                ),
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="articleblockstyle",
            name="exclude_from_global_alignment",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Opt this one block out of the Global editor's Alignment "
                    "control -- when set, saving a new global alignment (see "
                    "ArticleStyle.content_alignment) never overwrites this block's "
                    "own alignment above, even though every other alignment-"
                    "capable block in the article does get overwritten. Everything "
                    "else about this block (its own alignment value, font size, "
                    "box, etc.) is unaffected either way -- this only blocks the "
                    "bulk overwrite from touching this one row."
                ),
            ),
        ),
    ]
