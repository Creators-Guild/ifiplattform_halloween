"""Schema step 1 of 2 for moving ArticlePage's 21 whole-article styling
fields (hero image display, body/header side-padding/alignment/font-size/
background, TOC icon size) out to their own translation_key-keyed model,
ArticleStyle -- see that model's own docstring for the full why (same
"styling shouldn't differ between locale translations, only content
should" reasoning as ArticleBlockStyle's own re-key, migrations
0091-0093).

Creates ArticleStyle; leaves the 21 fields on ArticlePage untouched for
now so the follow-up data migration (0095) has something to backfill
from -- see 0096 for where they're actually removed.

The AlterField operations below (dropping each field's help_text) are a
harmless side effect of how this migration was generated -- temporarily
simplified copies of these fields were kept on ArticlePage just long
enough for `makemigrations` to see ArticleStyle as the only *real* change;
they carry no data or schema effect (SQLite doesn't store help_text in
the table itself) and are superseded by 0096's RemoveField anyway.
"""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifi_home_app", "0093_articleblockstyle_finalize_translation_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArticleStyle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("translation_key", models.UUIDField(unique=True)),
                (
                    "hero_image_position",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="right",
                        max_length=20,
                    ),
                ),
                (
                    "hero_image_width_rem",
                    models.FloatField(default=18, help_text="Width, in rem."),
                ),
                (
                    "hero_image_side_padding",
                    models.FloatField(
                        default=0, help_text="Left/right padding, in rem (0 = none)."
                    ),
                ),
                (
                    "hero_image_boxed",
                    models.BooleanField(
                        default=False,
                        help_text="Draw a border/box around the image, title and description.",
                    ),
                ),
                (
                    "hero_image_box_color",
                    models.CharField(
                        choices=[
                            ("bg-light", "Light"),
                            ("turq", "Turquoise"),
                            ("pink", "Pink"),
                            ("purple", "Purple"),
                            ("black", "Black"),
                            ("custom", "Custom (hex code)"),
                        ],
                        default="bg-light",
                        help_text="Box background color (only applies when 'boxed' is enabled).",
                        max_length=20,
                    ),
                ),
                (
                    "hero_image_box_custom_color",
                    models.CharField(
                        blank=True,
                        help_text="Hex code, e.g. #ff8800. Only used when color is set to 'Custom'.",
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                                "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                            )
                        ],
                    ),
                ),
                (
                    "hero_image_box_border_radius",
                    models.FloatField(
                        default=0.75,
                        help_text="Box corner rounding, in rem (0 = square corners). Only applies when 'boxed' is enabled.",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "content_side_padding",
                    models.FloatField(
                        default=0,
                        help_text="Left/right padding around the whole article body, in rem (0 = none). Applies on top of the site's own layout padding, and stacks with any per-block side padding inside it.",
                    ),
                ),
                (
                    "content_alignment",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="left",
                        help_text="Default alignment for any plain heading/paragraph content in the article body. Blocks with their own alignment option (styled text, images, multi-column) override this individually -- as does the title/intro/meta block above the body, which has its own separate alignment controls.",
                        max_length=20,
                    ),
                ),
                (
                    "content_font_size",
                    models.FloatField(
                        default=1,
                        help_text="Default font size for the body, in rem. Title, intro and meta have their own separate font size controls. Per-block font size (styled text) overrides this individually.",
                    ),
                ),
                (
                    "content_bg_enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Override the article body's default background color.",
                    ),
                ),
                (
                    "content_bg_color",
                    models.CharField(
                        choices=[
                            ("bg-light", "Light"),
                            ("turq", "Turquoise"),
                            ("pink", "Pink"),
                            ("purple", "Purple"),
                            ("black", "Black"),
                            ("custom", "Custom (hex code)"),
                        ],
                        default="bg-light",
                        help_text="Background color (only applies when the override above is enabled).",
                        max_length=20,
                    ),
                ),
                (
                    "content_bg_custom_color",
                    models.CharField(
                        blank=True,
                        help_text="Hex code, e.g. #ff8800. Only used when color is set to 'Custom'.",
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                                "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                            )
                        ],
                    ),
                ),
                (
                    "title_alignment",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="left",
                        help_text="Alignment for the article title.",
                        max_length=20,
                    ),
                ),
                (
                    "title_font_size",
                    models.FloatField(
                        default=2,
                        help_text="Font size for the article title, in rem. Independent from the body's own font size.",
                    ),
                ),
                (
                    "intro_alignment",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="left",
                        help_text="Alignment for the intro paragraph.",
                        max_length=20,
                    ),
                ),
                (
                    "intro_font_size",
                    models.FloatField(
                        default=1,
                        help_text="Font size for the intro paragraph, in rem. Independent from the body's own font size.",
                    ),
                ),
                (
                    "meta_alignment",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="left",
                        help_text="Alignment for the byline/date meta row.",
                        max_length=20,
                    ),
                ),
                (
                    "meta_font_size",
                    models.FloatField(
                        default=0.9,
                        help_text="Font size for the byline/date meta row, in rem. Independent from the body's own font size.",
                    ),
                ),
                (
                    "header_side_padding",
                    models.FloatField(
                        default=0,
                        help_text="Left/right padding around the title/meta/intro block, in rem (0 = none). Independent from the body's own side padding.",
                    ),
                ),
                (
                    "toc_icon_size",
                    models.FloatField(
                        default=1.3,
                        help_text='Size of the table-of-contents icon (the circular "contents" button next to the title), in rem. The button\'s own circle grows and shrinks along with it.',
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_alignment",
            field=models.CharField(
                choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
                default="left",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_bg_color",
            field=models.CharField(
                choices=[
                    ("bg-light", "Light"),
                    ("turq", "Turquoise"),
                    ("pink", "Pink"),
                    ("purple", "Purple"),
                    ("black", "Black"),
                    ("custom", "Custom (hex code)"),
                ],
                default="bg-light",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_bg_custom_color",
            field=models.CharField(
                blank=True,
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                        "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_bg_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_font_size",
            field=models.FloatField(default=1),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="content_side_padding",
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="header_side_padding",
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_box_border_radius",
            field=models.FloatField(
                default=0.75,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_box_color",
            field=models.CharField(
                choices=[
                    ("bg-light", "Light"),
                    ("turq", "Turquoise"),
                    ("pink", "Pink"),
                    ("purple", "Purple"),
                    ("black", "Black"),
                    ("custom", "Custom (hex code)"),
                ],
                default="bg-light",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_box_custom_color",
            field=models.CharField(
                blank=True,
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                        "Enter a valid hex color code, e.g. #ff8800 or #f80.",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_boxed",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_side_padding",
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="hero_image_width_rem",
            field=models.FloatField(default=18),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="intro_alignment",
            field=models.CharField(
                choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
                default="left",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="intro_font_size",
            field=models.FloatField(default=1),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="meta_alignment",
            field=models.CharField(
                choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
                default="left",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="meta_font_size",
            field=models.FloatField(default=0.9),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="title_alignment",
            field=models.CharField(
                choices=[("left", "Left"), ("center", "Center"), ("right", "Right")],
                default="left",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="title_font_size",
            field=models.FloatField(default=2),
        ),
        migrations.AlterField(
            model_name="articlepage",
            name="toc_icon_size",
            field=models.FloatField(default=1.3),
        ),
    ]
