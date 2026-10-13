"""Data step for moving ArticlePage's 21 styling fields to ArticleStyle
(see 0094's docstring for the full why). For every distinct translation_key
among ArticlePage rows, creates one ArticleStyle row copying the nb-locale
page's current field values -- nb is already this project's source of
truth for cross-locale conflicts (see ArticlePage.publish_target/the
ArticleBlockStyle re-key, migrations 0091-0093). Falls back to whichever
locale exists if a translation_key has no nb page at all (shouldn't
normally happen, since nb is where articles are meant to be created).

Verified against a real copy of the dev DB before being written: 15
distinct translation_keys, zero nb/en field-value conflicts (every
translation_key already has an nb page), so this is a straightforward
one-to-one copy for this database -- the "nb wins" tie-break exists for
correctness on any other database where a real conflict might exist.
"""

from django.db import migrations

STYLE_FIELDS = [
    "hero_image_position",
    "hero_image_width_rem",
    "hero_image_side_padding",
    "hero_image_boxed",
    "hero_image_box_color",
    "hero_image_box_custom_color",
    "hero_image_box_border_radius",
    "content_side_padding",
    "content_alignment",
    "content_font_size",
    "content_bg_enabled",
    "content_bg_color",
    "content_bg_custom_color",
    "title_alignment",
    "title_font_size",
    "intro_alignment",
    "intro_font_size",
    "meta_alignment",
    "meta_font_size",
    "header_side_padding",
    "toc_icon_size",
]


def backfill(apps, schema_editor):
    ArticlePage = apps.get_model("ifi_home_app", "ArticlePage")
    ArticleStyle = apps.get_model("ifi_home_app", "ArticleStyle")

    translation_keys = set(
        ArticlePage.objects.values_list("translation_key", flat=True)
    )
    for translation_key in translation_keys:
        pages = list(
            ArticlePage.objects.filter(translation_key=translation_key).select_related(
                "locale"
            )
        )
        nb_pages = [p for p in pages if p.locale.language_code == "nb"]
        source = nb_pages[0] if nb_pages else pages[0]
        ArticleStyle.objects.update_or_create(
            translation_key=translation_key,
            defaults={field: getattr(source, field) for field in STYLE_FIELDS},
        )


def unbackfill(apps, schema_editor):
    ArticleStyle = apps.get_model("ifi_home_app", "ArticleStyle")
    ArticleStyle.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "ifi_home_app",
            "0094_articlestyle_alter_articlepage_content_alignment_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
