"""Per-block style overrides and their effective-value resolution.

Design rationale/history: docs/claude_context/article_block_style.md"""

from django.db import models

from .constants import COLOR_CHOICES, CONTENT_ALIGNMENT_CHOICES, HEX_COLOR_VALIDATOR

BLOCK_STYLE_DEFAULTS = {
    "heading": {
        "alignment": "center",
        "font_size": 1.5,
        "side_padding": 0,
        "text_color": "",
        "text_custom_color": "",
        "text_shadow_enabled": False,
        "text_shadow_strength": 1,
        "text_shadow_color": "",
        "text_shadow_custom_color": "",
    },
    "paragraph": {
        "side_padding": 1,
        "alignment": "center",
        "font_size": 1,
        "text_color": "",
        "text_custom_color": "",
        "text_shadow_enabled": False,
        "text_shadow_strength": 1,
        "text_shadow_color": "",
        "text_shadow_custom_color": "",
    },
    "image": {"alignment": "center", "width_rem": 20, "side_padding": 0},
    "image_title": {
        "alignment": "center",
        "font_size": 0.85,
        "side_padding": 0,
        "text_color": "",
        "text_custom_color": "",
        "text_shadow_enabled": False,
        "text_shadow_strength": 1,
        "text_shadow_color": "",
        "text_shadow_custom_color": "",
    },
    "image_caption_body": {
        "alignment": "center",
        "font_size": 0.85,
        "side_padding": 0,
        "text_color": "",
        "text_custom_color": "",
        "text_shadow_enabled": False,
        "text_shadow_strength": 1,
        "text_shadow_color": "",
        "text_shadow_custom_color": "",
    },
    "article_card": {
        "width_rem": 22,
        "height_rem": 0,
        "list_style": False,
        "fixed_ratio": True,
    },
    "category_card": {"width_rem": 18, "height_rem": 0},
    "union_card": {"width_rem": 18, "height_rem": 0},
    "tool_card": {"width_rem": 20, "height_rem": 0},
    "multi_column": {"side_padding": 1, "gap": 2, "column_weight": 1},
    "article_header": {
        "side_padding": 0,
        "title_alignment": "left",
        "title_font_size": 2,
        "intro_alignment": "left",
        "intro_font_size": 1,
        "meta_alignment": "left",
        "meta_font_size": 0.9,
    },
    "hero_image": {
        "alignment": "right",
        "width_rem": 18,
        "side_padding": 0,
        "boxed": False,
        "box_color": "bg-light",
        "box_custom_color": "",
        "box_border_radius": 0.75,
        "shadow_enabled": True,
        "shadow_strength": 1,
        "shadow_color": "",
        "shadow_custom_color": "",
    },
    "toc_icon": {"toc_icon_size": 1.3},
    "box": {
        "enabled": False,
        "border_width": 0.125,
        "border_color": "black",
        "border_custom_color": "",
        "border_visible": True,
        "radius": 0.75,
        "bg_color": "bg-light",
        "bg_custom_color": "",
        "padding": 1,
        "margin": 0,
        "shadow_enabled": True,
        "shadow_strength": 1,
        "shadow_color": "",
        "shadow_custom_color": "",
    },
}
# Alias, not a copy -- see docs/claude_context/article_block_style.md.
BLOCK_STYLE_DEFAULTS["column_title"] = BLOCK_STYLE_DEFAULTS["heading"]


def _effective_box_style(override):
    """Effective border/background/radius/padding/margin for one
    block/column: its ArticleBlockStyle override where set, else
    BLOCK_STYLE_DEFAULTS['box']."""
    defaults = BLOCK_STYLE_DEFAULTS["box"]
    return {
        "enabled": (
            override.box_enabled
            if override and override.box_enabled is not None
            else defaults["enabled"]
        ),
        "border_width": (
            override.box_border_width
            if override and override.box_border_width is not None
            else defaults["border_width"]
        ),
        "border_color": (
            override.box_border_color
            if override and override.box_border_color
            else defaults["border_color"]
        ),
        "border_custom_color": (
            override.box_border_custom_color
            if override and override.box_border_custom_color
            else defaults["border_custom_color"]
        ),
        "border_visible": (
            override.box_border_visible
            if override and override.box_border_visible is not None
            else defaults["border_visible"]
        ),
        "radius": (
            override.box_radius
            if override and override.box_radius is not None
            else defaults["radius"]
        ),
        "bg_color": (
            override.box_bg_color
            if override and override.box_bg_color
            else defaults["bg_color"]
        ),
        "bg_custom_color": (
            override.box_bg_custom_color
            if override and override.box_bg_custom_color
            else defaults["bg_custom_color"]
        ),
        "padding": (
            override.box_padding
            if override and override.box_padding is not None
            else defaults["padding"]
        ),
        "margin": (
            override.box_margin
            if override and override.box_margin is not None
            else defaults["margin"]
        ),
        "shadow_enabled": (
            override.box_shadow_enabled
            if override and override.box_shadow_enabled is not None
            else defaults["shadow_enabled"]
        ),
        "shadow_strength": (
            override.box_shadow_strength
            if override and override.box_shadow_strength is not None
            else defaults["shadow_strength"]
        ),
        # offset/blur precomputed so templates don't do the math; 2/8 = the
        # original fixed shadow's own offset-y/blur-radius (strength=1
        # reproduces it exactly).
        "shadow_offset": 2
        * (
            override.box_shadow_strength
            if override and override.box_shadow_strength is not None
            else defaults["shadow_strength"]
        ),
        "shadow_blur": 8
        * (
            override.box_shadow_strength
            if override and override.box_shadow_strength is not None
            else defaults["shadow_strength"]
        ),
        "shadow_color": (
            override.box_shadow_color
            if override and override.box_shadow_color
            else defaults["shadow_color"]
        ),
        "shadow_custom_color": (
            override.box_shadow_custom_color
            if override and override.box_shadow_custom_color
            else defaults["shadow_custom_color"]
        ),
    }


def _effective_heading_style(override, defaults, font_size_multiplier=1.0):
    """Effective font_size/side_padding/alignment/box for one heading-shaped
    piece of text (an actual heading block, or anything reusing the same
    options -- e.g. a multi_column column's own title)."""
    raw_font_size = (
        override.font_size
        if override and override.font_size is not None
        else defaults["font_size"]
    )
    return {
        "font_size": raw_font_size,
        # scaled by ArticleStyle.content_font_size_multiplier; kept separate
        # from font_size so the multiplier never leaks into the raw value
        # the mini panel edits.
        "display_font_size": raw_font_size * font_size_multiplier,
        "side_padding": (
            override.side_padding
            if override and override.side_padding is not None
            else defaults["side_padding"]
        ),
        "alignment": (
            override.alignment
            if override and override.alignment
            else defaults["alignment"]
        ),
        "exclude_from_global_alignment": (
            bool(override.exclude_from_global_alignment) if override else False
        ),
        "text_color": (
            override.text_color
            if override and override.text_color
            else defaults["text_color"]
        ),
        "text_custom_color": (
            override.text_custom_color
            if override and override.text_custom_color
            else defaults["text_custom_color"]
        ),
        "text_shadow_enabled": (
            override.text_shadow_enabled
            if override and override.text_shadow_enabled is not None
            else defaults["text_shadow_enabled"]
        ),
        "text_shadow_strength": (
            override.text_shadow_strength
            if override and override.text_shadow_strength is not None
            else defaults["text_shadow_strength"]
        ),
        "text_shadow_offset": 1
        * (
            override.text_shadow_strength
            if override and override.text_shadow_strength is not None
            else defaults["text_shadow_strength"]
        ),
        "text_shadow_blur": 2
        * (
            override.text_shadow_strength
            if override and override.text_shadow_strength is not None
            else defaults["text_shadow_strength"]
        ),
        "text_shadow_color": (
            override.text_shadow_color
            if override and override.text_shadow_color
            else defaults["text_shadow_color"]
        ),
        "text_shadow_custom_color": (
            override.text_shadow_custom_color
            if override and override.text_shadow_custom_color
            else defaults["text_shadow_custom_color"]
        ),
        "box": _effective_box_style(override),
    }


def _effective_block_styles(
    body_stream, overrides_by_block_id, font_size_multiplier=1.0
):
    """Recursively walks a body StreamValue (or a column's own nested
    content) to {block_id: {...effective style}} for every heading/
    paragraph/image/multi_column block, including synthesized ids for an
    image's caption/title and a multi_column column's own title."""
    styles = {}
    for block in body_stream:
        block_id = str(block.id)
        override = overrides_by_block_id.get(block_id)
        if block.block_type in ("heading", "paragraph"):
            styles[block_id] = _effective_heading_style(
                override, BLOCK_STYLE_DEFAULTS[block.block_type], font_size_multiplier
            )
        elif block.block_type == "image":
            defaults = BLOCK_STYLE_DEFAULTS["image"]
            styles[block_id] = {
                "alignment": (
                    override.alignment
                    if override and override.alignment
                    else defaults["alignment"]
                ),
                "exclude_from_global_alignment": (
                    bool(override.exclude_from_global_alignment) if override else False
                ),
                "width_rem": (
                    override.width_rem
                    if override and override.width_rem is not None
                    else defaults["width_rem"]
                ),
                "side_padding": (
                    override.side_padding
                    if override and override.side_padding is not None
                    else defaults["side_padding"]
                ),
                "box": _effective_box_style(override),
            }
            caption_id = f"{block_id}-caption"
            caption_override = overrides_by_block_id.get(caption_id)
            styles[caption_id] = {
                "side_padding": (
                    caption_override.side_padding
                    if caption_override and caption_override.side_padding is not None
                    else 0
                ),
                "box": _effective_box_style(caption_override),
            }
            title_text_id = f"{block_id}-cap-title"
            styles[title_text_id] = _effective_heading_style(
                overrides_by_block_id.get(title_text_id),
                BLOCK_STYLE_DEFAULTS["image_title"],
                font_size_multiplier,
            )
            caption_text_id = f"{block_id}-cap-body"
            styles[caption_text_id] = _effective_heading_style(
                overrides_by_block_id.get(caption_text_id),
                BLOCK_STYLE_DEFAULTS["image_caption_body"],
                font_size_multiplier,
            )
        elif block.block_type in (
            "article_card",
            "category_card",
            "union_card",
            "tool_card",
        ):
            defaults = BLOCK_STYLE_DEFAULTS[block.block_type]
            card_style = {
                "width_rem": (
                    override.width_rem
                    if override and override.width_rem is not None
                    else defaults["width_rem"]
                ),
                "height_rem": (
                    override.height_rem
                    if override and override.height_rem is not None
                    else defaults["height_rem"]
                ),
            }
            if block.block_type == "article_card":
                card_style["list_style"] = (
                    override.list_style
                    if override and override.list_style is not None
                    else defaults["list_style"]
                )
                card_style["fixed_ratio"] = (
                    override.fixed_ratio
                    if override and override.fixed_ratio is not None
                    else defaults["fixed_ratio"]
                )
            styles[block_id] = card_style
        elif block.block_type == "multi_column":
            defaults = BLOCK_STYLE_DEFAULTS["multi_column"]
            own_weights = [defaults["column_weight"]] * len(block.value["columns"])
            override_weights = override.column_weights if override else None
            styles[block_id] = {
                "side_padding": (
                    override.side_padding
                    if override and override.side_padding is not None
                    else defaults["side_padding"]
                ),
                "gap": (
                    override.gap
                    if override and override.gap is not None
                    else defaults["gap"]
                ),
                "column_weights": (
                    override_weights
                    if override_weights and len(override_weights) == len(own_weights)
                    else own_weights
                ),
                "box": _effective_box_style(override),
            }
            for bound_column in block.value["columns"].bound_blocks:
                column_id = str(bound_column.id)
                column_override = overrides_by_block_id.get(column_id)
                styles[column_id] = {
                    "side_padding": (
                        column_override.side_padding
                        if column_override and column_override.side_padding is not None
                        else 0
                    ),
                    "box": _effective_box_style(column_override),
                }
                title_id = f"{column_id}-title"
                styles[title_id] = _effective_heading_style(
                    overrides_by_block_id.get(title_id),
                    BLOCK_STYLE_DEFAULTS["heading"],
                    font_size_multiplier,
                )
                styles.update(
                    _effective_block_styles(
                        bound_column.value["content"],
                        overrides_by_block_id,
                        font_size_multiplier,
                    )
                )
    return styles


def alignment_capable_block_ids(body_stream):
    """Every block_id (including synthesized ones) with its own 'alignment'
    field. Used by the global Alignment control's bulk-overwrite (see
    article_views.save_quick_style)."""
    styles = _effective_block_styles(body_stream, {})
    return [block_id for block_id, style in styles.items() if "alignment" in style]


class ArticleBlockStyle(models.Model):
    """A per-block style override (alignment/padding/font-size/gap/column
    weights/box) for one body block or multi_column sub-column, saved by the
    on-page block style panel -- deliberately a plain side table keyed by
    block_id rather than part of the StreamField/Wagtail revision system.
    Keyed by translation_key (shared across every locale copy of one
    article), not by a specific ArticlePage row.

    Design rationale/history: docs/claude_context/article_block_style.md"""

    translation_key = models.UUIDField()
    block_id = models.CharField(
        max_length=48
    )  # a few synthetic ids run longer than a plain block UUID

    side_padding = models.FloatField(null=True, blank=True)
    alignment = models.CharField(
        max_length=20, choices=CONTENT_ALIGNMENT_CHOICES, blank=True
    )
    exclude_from_global_alignment = models.BooleanField(
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
    )
    font_size = models.FloatField(null=True, blank=True)
    width_rem = models.FloatField(null=True, blank=True)
    gap = models.FloatField(null=True, blank=True)
    column_weights = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "multi_column only: one relative weight per column, same order "
            "as the block's own columns. Ignored (falls back to the "
            "block's own per-column weights) if its length no longer "
            "matches the current column count -- e.g. a column was added "
            "or removed in Wagtail after this override was saved."
        ),
    )

    box_enabled = models.BooleanField(null=True, blank=True)
    box_border_width = models.FloatField(null=True, blank=True)
    box_border_color = models.CharField(
        max_length=20, choices=COLOR_CHOICES, blank=True
    )
    box_border_custom_color = models.CharField(
        max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR]
    )
    box_border_visible = models.BooleanField(null=True, blank=True)
    box_radius = models.FloatField(null=True, blank=True)
    box_bg_color = models.CharField(max_length=20, choices=COLOR_CHOICES, blank=True)
    box_bg_custom_color = models.CharField(
        max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR]
    )
    # NOT part of _effective_box_style()'s dict -- unlike bg/border, text
    # color applies independent of whether the box itself is on.
    text_color = models.CharField(max_length=20, choices=COLOR_CHOICES, blank=True)
    text_custom_color = models.CharField(
        max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR]
    )
    text_shadow_enabled = models.BooleanField(null=True, blank=True)
    text_shadow_strength = models.FloatField(null=True, blank=True)
    text_shadow_color = models.CharField(
        max_length=20, choices=COLOR_CHOICES, blank=True
    )
    text_shadow_custom_color = models.CharField(
        max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR]
    )
    box_padding = models.FloatField(null=True, blank=True)
    box_margin = models.FloatField(null=True, blank=True)

    box_shadow_enabled = models.BooleanField(null=True, blank=True)
    box_shadow_strength = models.FloatField(null=True, blank=True)
    box_shadow_color = models.CharField(
        max_length=20, choices=COLOR_CHOICES, blank=True
    )
    box_shadow_custom_color = models.CharField(
        max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR]
    )

    # article_card only -- compact list row instead of a full card.
    list_style = models.BooleanField(null=True, blank=True)
    # 0/blank = auto height (content-driven).
    height_rem = models.FloatField(null=True, blank=True)
    # article_card only -- whether the image keeps its normal 8:5 aspect ratio.
    fixed_ratio = models.BooleanField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "block_id"],
                name="unique_article_block_style",
            )
        ]
