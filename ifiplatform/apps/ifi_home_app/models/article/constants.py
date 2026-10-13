"""Shared color/alignment/hex-validation constants used across the article
model split (article_style.py, article_block_style.py, article_pages.py) --
factored out on their own since they have no dependents of their own and
several of the other files need them."""

from django.core.validators import RegexValidator

HEX_COLOR_VALIDATOR = RegexValidator(
    r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
    "Enter a valid hex color code, e.g. #ff8800 or #f80.",
)

# shared fixed palette + custom-hex-fallback pattern, used anywhere a block
# needs a background/border color (image boxes, the box block).
COLOR_CHOICES = [
    ("bg-light", "Light"),
    ("turq", "Turquoise"),
    ("pink", "Pink"),
    ("purple", "Purple"),
    ("black", "Black"),
    ("custom", "Custom (hex code)"),
]

# module-level (not on ArticlePage) since ArticleStyle/ArticleBlockStyle
# also need these, and neither is a field on ArticlePage itself any more
# (styling moved out to ArticleStyle -- see that model's own docstring).
HERO_POSITION_CHOICES = [
    ("left", "Left"),
    ("center", "Center"),
    ("right", "Right"),
]

BOX_COLOR_CHOICES = [
    ("bg-light", "Light"),
    ("turq", "Turquoise"),
    ("pink", "Pink"),
    ("purple", "Purple"),
    ("black", "Black"),
    ("custom", "Custom (hex code)"),
]

CONTENT_ALIGNMENT_CHOICES = [
    ("left", "Left"),
    ("center", "Center"),
    ("right", "Right"),
]

TITLE_ALIGNMENT_CHOICES = CONTENT_ALIGNMENT_CHOICES
