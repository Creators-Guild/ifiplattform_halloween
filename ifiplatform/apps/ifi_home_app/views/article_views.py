"""API endpoints backing the on-page style panels on article pages
(padding/alignment/font size).

Design rationale/history: docs/claude_context/article_views.md"""

import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from wagtail.models import Page

from ifi_home_app.models.article_models import (
    BOX_COLOR_CHOICES,
    COLOR_CHOICES,
    CONTENT_ALIGNMENT_CHOICES,
    HERO_POSITION_CHOICES,
    HEX_COLOR_VALIDATOR,
    ArticleBlockStyle,
    ArticlePage,
    ArticleStyle,
    PageBannerStyle,
    alignment_capable_block_ids,
)

BOX_FIELDS = {
    "box_enabled",
    "box_border_width",
    "box_border_color",
    "box_border_custom_color",
    "box_border_visible",
    "box_radius",
    "box_bg_color",
    "box_bg_custom_color",
    "box_padding",
    "box_margin",
    "box_shadow_enabled",
    "box_shadow_strength",
    "box_shadow_color",
    "box_shadow_custom_color",
}

TEXT_COLOR_FIELDS = {
    "text_color",
    "text_custom_color",
    "text_shadow_enabled",
    "text_shadow_strength",
    "text_shadow_color",
    "text_shadow_custom_color",
}

EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD = {"exclude_from_global_alignment"}

# Per-block-type allow-list for save_block_style. See
# docs/claude_context/article_views.md for what each entry means.
BLOCK_STYLE_FIELDS = {
    "heading": {"side_padding", "alignment", "font_size"}
    | BOX_FIELDS
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "paragraph": {"side_padding", "alignment", "font_size"}
    | BOX_FIELDS
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "image": {"alignment", "width_rem", "side_padding"}
    | BOX_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "article_card": {"width_rem", "height_rem", "list_style", "fixed_ratio"},
    "category_card": {"width_rem", "height_rem"},
    "union_card": {"width_rem", "height_rem"},
    "tool_card": {"width_rem", "height_rem"},
    "image_caption": {"side_padding"} | BOX_FIELDS,
    "image_title": {"side_padding", "alignment", "font_size"}
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "image_caption_body": {"side_padding", "alignment", "font_size"}
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "multi_column": {"side_padding", "gap", "column_weights"} | BOX_FIELDS,
    "column": {"side_padding"} | BOX_FIELDS,
    "column_title": {"alignment", "font_size"}
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "title": {"side_padding"}
    | BOX_FIELDS
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "meta": {"side_padding"}
    | BOX_FIELDS
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "intro": {"side_padding"}
    | BOX_FIELDS
    | TEXT_COLOR_FIELDS
    | EXCLUDE_FROM_GLOBAL_ALIGNMENT_FIELD,
    "article_header": set(BOX_FIELDS),
}


@require_POST
def save_quick_style(request, page_id):
    """Upsert onto the page's shared ArticleStyle row. Live immediately, no
    Wagtail revision/publish. apply_alignment_to_blocks and reset_header are
    the two destructive exceptions -- see docs/claude_context/article_views.md."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        side_padding = float(data["content_side_padding"])
        alignment = data["content_alignment"]
        font_size_multiplier = float(data["content_font_size_multiplier"])
        bg_enabled = bool(data["content_bg_enabled"])
        bg_color = data["content_bg_color"]
        bg_custom_color = data.get("content_bg_custom_color") or ""
        apply_alignment_to_blocks = bool(data.get("apply_alignment_to_blocks"))
        reset_header = bool(data.get("reset_header"))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    if alignment not in dict(CONTENT_ALIGNMENT_CHOICES):
        return JsonResponse({"error": "Invalid alignment."}, status=400)

    if not 0.5 <= font_size_multiplier <= 2:
        return JsonResponse(
            {"error": "Invalid content_font_size_multiplier."}, status=400
        )

    if bg_color not in dict(COLOR_CHOICES):
        return JsonResponse({"error": "Invalid content_bg_color."}, status=400)

    if bg_custom_color:
        try:
            HEX_COLOR_VALIDATOR(bg_custom_color)
        except ValidationError:
            return JsonResponse(
                {"error": "Invalid content_bg_custom_color."}, status=400
            )

    style = page.style
    style.content_side_padding = side_padding
    style.content_alignment = alignment
    style.content_font_size_multiplier = font_size_multiplier
    style.content_bg_enabled = bg_enabled
    style.content_bg_color = bg_color
    style.content_bg_custom_color = bg_custom_color

    if reset_header:
        # the one part of "reset to default" that content_side_padding/
        # content_font_size_multiplier above can't reach on their own --
        # those two only ever stack/multiply with these (see their own
        # docstrings), never overwrite them, so a real reset has to touch
        # these fields directly instead. Same defaults quick_style_defaults()
        # already exposes to the Reset button's own data-default-* attributes
        # (article_quick_style_panel.html) -- one source of truth either way.
        header_defaults = ArticleStyle.quick_style_defaults()
        style.header_side_padding = header_defaults["header_padding"]
        style.title_font_size = header_defaults["title_font_size"]
        style.meta_font_size = header_defaults["meta_font_size"]
        style.intro_font_size = header_defaults["intro_font_size"]
        # title/meta/intro alignment too -- set directly here rather than
        # relying solely on apply_alignment_to_blocks below, which only
        # touches them when content_alignment itself actually changed this
        # session (alignmentChanged in article_quick_style.js), and even
        # then sets all three to content_alignment's own value rather than
        # each field's own default. Each field's own default here instead
        # (can differ from content_alignment's and from each other's, see
        # their own docstrings) -- apply_alignment_to_blocks's header loop
        # is skipped below whenever reset_header is set, so it can't
        # immediately overwrite these with content_alignment's value.
        style.title_alignment = header_defaults["title_alignment"]
        style.meta_alignment = header_defaults["meta_alignment"]
        style.intro_alignment = header_defaults["intro_alignment"]

    style.save()

    if apply_alignment_to_blocks:
        excluded_ids = set(
            ArticleBlockStyle.objects.filter(
                translation_key=page.translation_key, exclude_from_global_alignment=True
            ).values_list("block_id", flat=True)
        )
        block_ids = [
            block_id
            for block_id in alignment_capable_block_ids(page.body)
            if block_id not in excluded_ids
        ]
        ArticleBlockStyle.objects.bulk_create(
            [
                ArticleBlockStyle(
                    translation_key=page.translation_key,
                    block_id=block_id,
                    alignment=alignment,
                )
                for block_id in block_ids
            ],
            update_conflicts=True,
            unique_fields=["translation_key", "block_id"],
            update_fields=["alignment"],
        )

        # Skipped when reset_header already set these above -- to each
        # field's own default, not content_alignment's value, see that
        # block's own comment. Running this loop too would immediately
        # overwrite that with content_alignment's value instead.
        if not reset_header:
            header_alignment_fields = {
                "article-title": "title_alignment",
                "article-meta": "meta_alignment",
                "article-intro": "intro_alignment",
            }
            style_changed = False
            for header_block_id, style_field in header_alignment_fields.items():
                if header_block_id not in excluded_ids:
                    setattr(style, style_field, alignment)
                    style_changed = True
            if style_changed:
                style.save()

    return JsonResponse({"ok": True})


@require_POST
def save_block_style(request, page_id):
    """Upsert a single block's ArticleBlockStyle override -- outside
    Wagtail's StreamField/revision/publish system entirely, live
    immediately, no draft step."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        block_id = data["block_id"]
        block_type = data["block_type"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    allowed_fields = BLOCK_STYLE_FIELDS.get(block_type)
    if not allowed_fields or not block_id:
        return JsonResponse({"error": "Invalid block type."}, status=400)

    defaults = {}
    try:
        if "side_padding" in allowed_fields and data.get("side_padding") is not None:
            defaults["side_padding"] = float(data["side_padding"])
        if "font_size" in allowed_fields and data.get("font_size") is not None:
            defaults["font_size"] = float(data["font_size"])
        if "width_rem" in allowed_fields and data.get("width_rem") is not None:
            defaults["width_rem"] = float(data["width_rem"])
        if "height_rem" in allowed_fields and data.get("height_rem") is not None:
            defaults["height_rem"] = float(data["height_rem"])
        if "gap" in allowed_fields and data.get("gap") is not None:
            defaults["gap"] = float(data["gap"])
        if (
            "column_weights" in allowed_fields
            and data.get("column_weights") is not None
        ):
            defaults["column_weights"] = [float(w) for w in data["column_weights"]]
        if (
            "box_border_width" in allowed_fields
            and data.get("box_border_width") is not None
        ):
            defaults["box_border_width"] = float(data["box_border_width"])
        if "box_radius" in allowed_fields and data.get("box_radius") is not None:
            defaults["box_radius"] = float(data["box_radius"])
        if "box_padding" in allowed_fields and data.get("box_padding") is not None:
            defaults["box_padding"] = float(data["box_padding"])
        if "box_margin" in allowed_fields and data.get("box_margin") is not None:
            defaults["box_margin"] = float(data["box_margin"])
        if (
            "box_shadow_strength" in allowed_fields
            and data.get("box_shadow_strength") is not None
        ):
            defaults["box_shadow_strength"] = float(data["box_shadow_strength"])
        if (
            "text_shadow_strength" in allowed_fields
            and data.get("text_shadow_strength") is not None
        ):
            defaults["text_shadow_strength"] = float(data["text_shadow_strength"])
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    # Matches the on-page slider's own range -- a direct POST could
    # otherwise set a value the mobile CSS resets can't fully undo.
    for field_name, bounds in (
        ("width_rem", (4, 60)),
        ("height_rem", (0, 40)),
        ("box_shadow_strength", (0, 3)),
        ("text_shadow_strength", (0, 3)),
    ):
        value = defaults.get(field_name)
        if value is not None and not bounds[0] <= value <= bounds[1]:
            return JsonResponse({"error": f"Invalid {field_name}."}, status=400)

    if "alignment" in allowed_fields and data.get("alignment") is not None:
        alignment = data["alignment"]
        if alignment not in dict(CONTENT_ALIGNMENT_CHOICES):
            return JsonResponse({"error": "Invalid alignment."}, status=400)
        defaults["alignment"] = alignment

    if "box_enabled" in allowed_fields and data.get("box_enabled") is not None:
        defaults["box_enabled"] = bool(data["box_enabled"])
    if (
        "box_border_visible" in allowed_fields
        and data.get("box_border_visible") is not None
    ):
        defaults["box_border_visible"] = bool(data["box_border_visible"])
    if (
        "box_shadow_enabled" in allowed_fields
        and data.get("box_shadow_enabled") is not None
    ):
        defaults["box_shadow_enabled"] = bool(data["box_shadow_enabled"])
    if (
        "text_shadow_enabled" in allowed_fields
        and data.get("text_shadow_enabled") is not None
    ):
        defaults["text_shadow_enabled"] = bool(data["text_shadow_enabled"])
    if "list_style" in allowed_fields and data.get("list_style") is not None:
        defaults["list_style"] = bool(data["list_style"])
    if "fixed_ratio" in allowed_fields and data.get("fixed_ratio") is not None:
        defaults["fixed_ratio"] = bool(data["fixed_ratio"])
    if (
        "exclude_from_global_alignment" in allowed_fields
        and data.get("exclude_from_global_alignment") is not None
    ):
        defaults["exclude_from_global_alignment"] = bool(
            data["exclude_from_global_alignment"]
        )

    # "" is a real value for these, not "unset" -- see
    # docs/claude_context/article_views.md.
    for color_field, custom_field in (
        ("box_border_color", "box_border_custom_color"),
        ("box_bg_color", "box_bg_custom_color"),
        ("text_color", "text_custom_color"),
        ("box_shadow_color", "box_shadow_custom_color"),
        ("text_shadow_color", "text_shadow_custom_color"),
    ):
        if color_field in allowed_fields and data.get(color_field) is not None:
            color = data[color_field]
            if color and color not in dict(COLOR_CHOICES):
                return JsonResponse({"error": f"Invalid {color_field}."}, status=400)
            defaults[color_field] = color
        if custom_field in allowed_fields and data.get(custom_field) is not None:
            custom_color = data[custom_field]
            if custom_color:
                try:
                    HEX_COLOR_VALIDATOR(custom_color)
                except ValidationError:
                    return JsonResponse(
                        {"error": f"Invalid {custom_field}."}, status=400
                    )
            defaults[custom_field] = custom_color

    ArticleBlockStyle.objects.update_or_create(
        translation_key=page.translation_key, block_id=block_id, defaults=defaults
    )

    return JsonResponse({"ok": True})


@require_POST
def save_header_style(request, page_id):
    """Upsert title/intro/meta alignment/font-size + header_side_padding
    onto the page's shared ArticleStyle row."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        title_alignment = data["title_alignment"]
        intro_alignment = data["intro_alignment"]
        meta_alignment = data["meta_alignment"]
        header_side_padding = float(data["header_side_padding"])
        title_font_size = float(data["title_font_size"])
        intro_font_size = float(data["intro_font_size"])
        meta_font_size = float(data["meta_font_size"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    valid_alignments = dict(CONTENT_ALIGNMENT_CHOICES)
    for value in (title_alignment, intro_alignment, meta_alignment):
        if value not in valid_alignments:
            return JsonResponse({"error": "Invalid alignment."}, status=400)

    style = page.style
    style.title_alignment = title_alignment
    style.intro_alignment = intro_alignment
    style.meta_alignment = meta_alignment
    style.header_side_padding = header_side_padding
    style.title_font_size = title_font_size
    style.intro_font_size = intro_font_size
    style.meta_font_size = meta_font_size
    style.save()

    return JsonResponse({"ok": True})


@require_POST
def save_hero_image_style(request, page_id):
    """Upsert hero image position/size/box fields onto the page's shared
    ArticleStyle row."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        alignment = data["alignment"]
        width_rem = float(data["width_rem"])
        side_padding = float(data["side_padding"])
        boxed = bool(data["boxed"])
        box_color = data["box_color"]
        box_custom_color = data.get("box_custom_color") or ""
        box_border_radius = float(data["box_border_radius"])
        shadow_enabled = bool(data["shadow_enabled"])
        shadow_strength = float(data["shadow_strength"])
        shadow_color = data.get("shadow_color") or ""
        shadow_custom_color = data.get("shadow_custom_color") or ""
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    if alignment not in dict(HERO_POSITION_CHOICES):
        return JsonResponse({"error": "Invalid alignment."}, status=400)

    if not 4 <= width_rem <= 60:
        return JsonResponse({"error": "Invalid width_rem."}, status=400)

    if box_color not in dict(BOX_COLOR_CHOICES):
        return JsonResponse({"error": "Invalid box_color."}, status=400)

    if box_custom_color:
        try:
            HEX_COLOR_VALIDATOR(box_custom_color)
        except ValidationError:
            return JsonResponse({"error": "Invalid box_custom_color."}, status=400)

    if not 0 <= box_border_radius <= 5:
        return JsonResponse({"error": "Invalid box_border_radius."}, status=400)

    if not 0 <= shadow_strength <= 3:
        return JsonResponse({"error": "Invalid shadow_strength."}, status=400)

    if shadow_color and shadow_color not in dict(BOX_COLOR_CHOICES):
        return JsonResponse({"error": "Invalid shadow_color."}, status=400)

    if shadow_custom_color:
        try:
            HEX_COLOR_VALIDATOR(shadow_custom_color)
        except ValidationError:
            return JsonResponse({"error": "Invalid shadow_custom_color."}, status=400)

    style = page.style
    style.hero_image_position = alignment
    style.hero_image_width_rem = width_rem
    style.hero_image_side_padding = side_padding
    style.hero_image_boxed = boxed
    style.hero_image_box_color = box_color
    style.hero_image_box_custom_color = box_custom_color
    style.hero_image_box_border_radius = box_border_radius
    style.hero_image_box_shadow_enabled = shadow_enabled
    style.hero_image_box_shadow_strength = shadow_strength
    style.hero_image_box_shadow_color = shadow_color
    style.hero_image_box_shadow_custom_color = shadow_custom_color
    style.save()

    return JsonResponse({"ok": True})


@require_POST
def save_toc_icon_style(request, page_id):
    """Upsert toc_icon_size onto the page's shared ArticleStyle row."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        toc_icon_size = float(data["toc_icon_size"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    style = page.style
    style.toc_icon_size = toc_icon_size
    style.save()

    return JsonResponse({"ok": True})


@require_POST
def publish_page(request, page_id):
    """Publish the latest draft revision of one ArticlePage from its
    front-end URL, bypassing wagtail-admin. See
    docs/claude_context/article_views.md."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_publish_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to publish this page."}, status=403
        )

    revision = page.get_latest_revision()
    if revision is None:
        return JsonResponse({"error": "This page has no draft to publish."}, status=400)

    revision.publish(user=request.user)

    return JsonResponse({"ok": True})


@require_POST
def unpublish_page(request, page_id):
    """Unpublish one ArticlePage from its front-end URL."""
    page = get_object_or_404(ArticlePage, pk=page_id)

    if not page.can_unpublish_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to unpublish this page."}, status=403
        )

    page.unpublish(user=request.user)

    return JsonResponse({"ok": True})


@require_POST
def save_banner_style(request, page_id):
    """Upsert onto the page's shared PageBannerStyle row. Not
    ArticlePage-specific -- shared by CategoryPage/ArticleIndexPage/
    StudentUnionCategoryPage via BannerStyleMixin."""
    page = get_object_or_404(Page, pk=page_id).specific

    if not page.can_edit_in_editor_mode(request.user):
        return JsonResponse(
            {"error": "You don't have permission to edit this page."}, status=403
        )

    try:
        data = json.loads(request.body)
        show_banner = bool(data["show_banner"])
        banner_color = data.get("banner_color") or ""
        banner_dot_color = data.get("banner_dot_color") or ""
        banner_text_color = data.get("banner_text_color") or ""
        # blank/0 both mean "auto" -- stored as None either way.
        width_rem = (
            float(data["banner_width_rem"]) if data.get("banner_width_rem") else None
        )
        height_rem = (
            float(data["banner_height_rem"]) if data.get("banner_height_rem") else None
        )
        font_size = (
            float(data["banner_font_size"]) if data.get("banner_font_size") else None
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid data."}, status=400)

    for value, field_name in (
        (banner_color, "banner_color"),
        (banner_dot_color, "banner_dot_color"),
        (banner_text_color, "banner_text_color"),
    ):
        if value:
            try:
                HEX_COLOR_VALIDATOR(value)
            except ValidationError:
                return JsonResponse({"error": f"Invalid {field_name}."}, status=400)

    for value, field_name, bounds in (
        (width_rem, "banner_width_rem", (1, 100)),
        (height_rem, "banner_height_rem", (1, 60)),
        (font_size, "banner_font_size", (0.5, 6)),
    ):
        if value is not None and not bounds[0] <= value <= bounds[1]:
            return JsonResponse({"error": f"Invalid {field_name}."}, status=400)

    style = PageBannerStyle.objects.get_or_create(translation_key=page.translation_key)[
        0
    ]
    style.show_banner = show_banner
    style.banner_color = banner_color
    style.banner_dot_color = banner_dot_color
    style.banner_text_color = banner_text_color
    style.banner_width_rem = width_rem
    style.banner_height_rem = height_rem
    style.banner_font_size = font_size
    style.save()

    return JsonResponse({"ok": True})
