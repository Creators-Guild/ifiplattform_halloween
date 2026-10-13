"""Backward-compatible re-export shim -- kept as a real module (not deleted)
because three historical migrations (0028_studentunioncategorypage_unionpage,
0029_toolpage, 0117_eventindexpage_eventpage) hard-code
`ifi_home_app.models.article_models.TranslationWarningMixin` in their
`bases=` tuples, and every existing view/templatetag/test/seed-script import
already targets this exact path. The actual model/logic code now lives in
page_mixins.py (shared with models/event/) and the models/article/
package (constants.py/blocks.py/style.py/block_style.py/pages.py/
unions.py/tools.py) -- see those files for the real definitions."""

from .article.constants import (
    BOX_COLOR_CHOICES,
    COLOR_CHOICES,
    CONTENT_ALIGNMENT_CHOICES,
    HERO_POSITION_CHOICES,
    HEX_COLOR_VALIDATOR,
    TITLE_ALIGNMENT_CHOICES,
)
from .page_mixins import (
    BannerStyleMixin,
    EditorModeMixin,
    PageBannerStyle,
    TranslationWarningMixin,
    editor_mode_allowed,
)
from .article.blocks import (
    article_card_block,
    article_image_block,
    article_paragraph_block,
    category_card_block,
    tool_card_block,
    union_card_block,
    union_group_block,
)
from .article.style import ArticleStyle
from .article.block_style import (
    BLOCK_STYLE_DEFAULTS,
    ArticleBlockStyle,
    alignment_capable_block_ids,
)
from .article.pages import (
    ArticleIndexPage,
    ArticlePage,
    CategoryPage,
    get_section_index,
)
from .article.unions import StudentUnionCategoryPage, UnionPage
from .article.tools import ToolPage

__all__ = [
    "BOX_COLOR_CHOICES",
    "COLOR_CHOICES",
    "CONTENT_ALIGNMENT_CHOICES",
    "HERO_POSITION_CHOICES",
    "HEX_COLOR_VALIDATOR",
    "TITLE_ALIGNMENT_CHOICES",
    "BannerStyleMixin",
    "EditorModeMixin",
    "PageBannerStyle",
    "TranslationWarningMixin",
    "editor_mode_allowed",
    "article_card_block",
    "article_image_block",
    "article_paragraph_block",
    "category_card_block",
    "tool_card_block",
    "union_card_block",
    "union_group_block",
    "ArticleStyle",
    "BLOCK_STYLE_DEFAULTS",
    "ArticleBlockStyle",
    "alignment_capable_block_ids",
    "ArticleIndexPage",
    "ArticlePage",
    "CategoryPage",
    "get_section_index",
    "StudentUnionCategoryPage",
    "UnionPage",
    "ToolPage",
]
