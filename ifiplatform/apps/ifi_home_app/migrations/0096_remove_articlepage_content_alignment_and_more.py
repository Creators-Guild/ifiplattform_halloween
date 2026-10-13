"""Schema step 2 of 2 for moving ArticlePage's styling out to ArticleStyle
(see 0094's docstring for the full why) -- removes the 21 fields for real,
now that every translation_key has a backfilled ArticleStyle row (0095).

Forward-only in practice, same reasoning already documented on 0093:
Django's SQLite reverse for RemoveField re-adds each column empty, with no
way to repopulate the values this migration didn't capture anywhere
reversible. Recovery, if ever needed, is restore-from-backup-and-reapply-
forward, not reverse-in-place.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0095_backfill_articlestyle"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="articlepage",
            name="content_alignment",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="content_bg_color",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="content_bg_custom_color",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="content_bg_enabled",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="content_font_size",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="content_side_padding",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="header_side_padding",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_box_border_radius",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_box_color",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_box_custom_color",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_boxed",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_position",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_side_padding",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="hero_image_width_rem",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="intro_alignment",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="intro_font_size",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="meta_alignment",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="meta_font_size",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="title_alignment",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="title_font_size",
        ),
        migrations.RemoveField(
            model_name="articlepage",
            name="toc_icon_size",
        ),
    ]
