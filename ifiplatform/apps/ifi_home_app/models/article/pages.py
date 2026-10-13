"""ArticlePage, CategoryPage and ArticleIndexPage.

Design rationale/history: docs/claude_context/article_pages.md"""

from django.conf import settings
from django.db import models
from django.http import Http404
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Locale, Page
from wagtail.url_routing import RouteResult

from .blocks import _body_content_blocks, _iter_toc_entries
from .block_style import (
    BLOCK_STYLE_DEFAULTS,
    ArticleBlockStyle,
    _effective_block_styles,
    _effective_box_style,
)
from .style import ArticleStyle
from ..page_mixins import (
    BannerStyleMixin,
    EditorModeMixin,
    TranslationWarningMixin,
    editor_mode_allowed,
)
from .tools import ToolPage
from .unions import StudentUnionCategoryPage
from ...translation.sync import SOURCE_LANGUAGE_CODE


def _split_categories_by_season(categories):
    """Split live categories into (main, seasonal) lists, seasonal filtered to currently-active ones."""
    main = [c for c in categories if not c.is_seasonal]
    seasonal = [c for c in categories if c.is_seasonal and c.is_currently_active]
    return main, seasonal


def _articles_including_drafts_for_editor(queryset, listing_page, user):
    """`queryset` with draft articles included too if `user` can edit
    `listing_page`. See docs/claude_context/article_pages.md."""
    if listing_page.permissions_for_user(user).can_edit():
        return queryset
    return queryset.live()


def get_section_index(section):
    """The site's live ArticleIndexPage for `section` ('info_articles' or 'news'),
    in the active locale."""
    return (
        ArticleIndexPage.objects.live()
        .filter(locale=Locale.get_active(), section=section)
        .first()
    )


# Current tree: ArticleIndexPage -> CategoryPage -> ArticlePage


class ArticlePage(
    EditorModeMixin, TranslationWarningMixin, Page
):  # pylint: disable=too-many-ancestors
    """A single article page, published under a CategoryPage."""

    template = "info_articles/pages/article_page.html"

    intro = RichTextField(blank=True)
    # hero_image itself and its title/alt/caption are content; how it's
    # displayed (position/width/padding/box) is styling, see ArticleStyle.
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_image_title = models.CharField(
        max_length=250,
        blank=True,
        help_text="Shown under the image, above the caption. Leave blank for none.",
    )
    hero_image_alt = models.CharField(
        max_length=250,
        blank=True,
        help_text="Accessible description of the image, for screen readers -- not shown visibly. Leave blank to use the image's own title.",
    )
    hero_image_caption = models.CharField(max_length=250, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    ATTRIBUTION_CHOICES = [
        ("real_name", "Real name"),
        ("nickname", "Nickname"),
    ]
    author_attribution = models.CharField(
        max_length=20,
        choices=ATTRIBUTION_CHOICES,
        default="real_name",
        help_text="Which identity to credit the author under, if they've set a nickname.",
    )
    # Written by account_app's delete_account_view once author goes NULL --
    # see docs/claude_context/article_pages.md for the fallback chain.
    author_display_name = models.CharField(max_length=150, blank=True)
    published_date = models.DateField()
    show_on_homepage = models.BooleanField(
        default=True,
        help_text="Whether this article can be suggested on the homepage (newsbar/articles bar).",
    )

    body = StreamField(
        _body_content_blocks(),
        use_json_field=True,
    )

    # No FieldPanel for styling -- edited entirely on-page via editor mode
    # (article_block_style.js/article_quick_style.js).
    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("hero_image"),
        FieldPanel("hero_image_title"),
        FieldPanel("hero_image_alt"),
        FieldPanel("hero_image_caption"),
        FieldPanel("author"),
        FieldPanel("author_attribution"),
        FieldPanel("published_date"),
        FieldPanel("show_on_homepage"),
        FieldPanel("body"),
    ]

    parent_page_types = [
        "ifi_home_app.CategoryPage",
        "ifi_home_app.ArticleIndexPage",
    ]
    subpage_types = []

    @classmethod
    def can_create_at(cls, parent):
        """See docs/claude_context/article_pages.md (hub-index gating)."""
        if not super().can_create_at(parent):
            return False
        if isinstance(parent, ArticleIndexPage):
            return parent.section != "hub"
        return True

    @property
    def category(self):
        """The CategoryPage this article lives under, or None if it was
        created directly under an ArticleIndexPage instead."""
        parent = self.get_parent().specific
        return parent if isinstance(parent, CategoryPage) else None

    @property
    def display_author_name(self):
        """See docs/claude_context/article_pages.md for the full fallback
        chain once `author` is deleted."""
        if self.author_id:
            if self.author_attribution == "nickname":
                nickname = (
                    getattr(self.author, "profile", None)
                    and self.author.profile.nickname
                )
                if nickname:
                    return nickname
            return self.author.get_full_name() or self.author.username
        if self.author_display_name == "unknown":
            return _("Unknown")
        return self.author_display_name or None

    def route(self, request, path_components):
        """A draft article stays reachable at its normal URL for anyone
        with edit rights. See docs/claude_context/article_pages.md."""
        if not path_components and not self.live:
            if self.can_edit_in_editor_mode(request.user):
                return RouteResult(self)
            raise Http404
        return super().route(request, path_components)

    @cached_property
    def style(self):
        """This article's shared ArticleStyle row, keyed by translation_key
        (same row across every locale). Created with defaults on first
        access."""
        return ArticleStyle.objects.get_or_create(translation_key=self.translation_key)[
            0
        ]

    # aliases the shared constant so existing SOURCE_LANGUAGE_CODE
    # references keep working unchanged.
    SOURCE_LANGUAGE_CODE = SOURCE_LANGUAGE_CODE

    @property
    def publish_target(self):
        """The nb-locale copy -- publish/unpublish always acts on this one
        regardless of viewed locale. See docs/claude_context/article_pages.md."""
        target = self.style_target
        if target.locale.language_code == self.SOURCE_LANGUAGE_CODE:
            return target
        nb_locale = Locale.objects.filter(
            language_code=self.SOURCE_LANGUAGE_CODE
        ).first()
        if nb_locale is None:
            return target
        return target.get_translation_or_none(nb_locale) or target

    def can_publish_in_editor_mode(self, user):
        return editor_mode_allowed(self.publish_target, user, "publish")

    def can_unpublish_in_editor_mode(self, user):
        return editor_mode_allowed(self.publish_target, user, "unpublish")

    @property
    def toc_entries(self):
        return list(_iter_toc_entries(self.body))

    @property
    def has_headings(self):
        return bool(self.toc_entries)

    def get_context(self, request, *args, **kwargs):
        """See docs/claude_context/article_pages.md for what each context
        key is for and the title/meta/intro pseudo-id styling."""
        context = super().get_context(request, *args, **kwargs)
        context["can_edit_style"] = self.can_edit_in_editor_mode(request.user)
        context["quick_style_defaults"] = ArticleStyle.quick_style_defaults()
        context["page_is_live"] = self.live
        context["page_has_unpublished_changes"] = self.has_unpublished_changes
        context["page_has_pending_publish"] = (
            not self.live
        ) or self.has_unpublished_changes
        context["can_publish_page"] = self.can_publish_in_editor_mode(request.user)
        context["can_unpublish_page"] = self.can_unpublish_in_editor_mode(request.user)
        context["can_sync_mirrored_page"] = self.can_sync_mirrored_page(request.user)
        context["translation_nudge"] = self.translation_nudge(request.user)
        overrides_by_block_id = {
            style.block_id: style
            for style in ArticleBlockStyle.objects.filter(
                translation_key=self.translation_key
            )
        }
        block_styles = _effective_block_styles(
            self.body,
            overrides_by_block_id,
            font_size_multiplier=self.style.content_font_size_multiplier,
        )
        for pseudo_id in ("article-title", "article-meta", "article-intro"):
            override = overrides_by_block_id.get(pseudo_id)
            block_styles[pseudo_id] = {
                "side_padding": (
                    override.side_padding
                    if override and override.side_padding is not None
                    else 0
                ),
                "box": _effective_box_style(override),
                "text_color": (
                    override.text_color if override and override.text_color else ""
                ),
                "text_custom_color": (
                    override.text_custom_color
                    if override and override.text_custom_color
                    else ""
                ),
                "text_shadow_enabled": (
                    bool(override.text_shadow_enabled) if override else False
                ),
                "text_shadow_strength": (
                    override.text_shadow_strength
                    if override and override.text_shadow_strength is not None
                    else 1
                ),
                "text_shadow_offset": 1
                * (
                    override.text_shadow_strength
                    if override and override.text_shadow_strength is not None
                    else 1
                ),
                "text_shadow_blur": 2
                * (
                    override.text_shadow_strength
                    if override and override.text_shadow_strength is not None
                    else 1
                ),
                "text_shadow_color": (
                    override.text_shadow_color
                    if override and override.text_shadow_color
                    else ""
                ),
                "text_shadow_custom_color": (
                    override.text_shadow_custom_color
                    if override and override.text_shadow_custom_color
                    else ""
                ),
            }
        block_styles["article-header"] = {
            "box": _effective_box_style(overrides_by_block_id.get("article-header")),
        }
        context["block_styles"] = block_styles
        context["block_style_defaults"] = BLOCK_STYLE_DEFAULTS
        return context


class CategoryPage(
    EditorModeMixin, BannerStyleMixin, TranslationWarningMixin, Page
):  # pylint: disable=too-many-ancestors
    """A category of articles, optionally shown only during a specific date range."""

    template = "info_articles/pages/article_category_page.html"

    intro = RichTextField(blank=True)
    general_info = RichTextField(
        blank=True,
        help_text="Optional -- a short paragraph of general information about this category, shown below the intro.",
    )

    COLOR_CHOICES = [
        ("turq", "Turquoise"),
        ("pink", "Pink"),
        ("purple", "Purple"),
    ]

    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="turq",
        help_text="Accent color used for this category and its articles.",
    )

    # blank = always shown ("main" category); set = shown only while today
    # falls within the range.
    active_from = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for a category that should always be visible.",
    )
    active_until = models.DateField(null=True, blank=True)

    show_nested_tools = models.BooleanField(
        default=False,
        help_text=(
            "Show tools from every subcategory below this one here too "
            "(children, grandchildren, ...), not just this category's own "
            "direct tools."
        ),
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("general_info"),
        FieldPanel("color"),
        FieldPanel("active_from"),
        FieldPanel("active_until"),
        FieldPanel("show_nested_tools"),
    ]

    parent_page_types = ["ifi_home_app.ArticleIndexPage", "ifi_home_app.CategoryPage"]
    subpage_types = [
        "ifi_home_app.ArticlePage",
        "ifi_home_app.CategoryPage",
        "ifi_home_app.StudentUnionCategoryPage",
        "ifi_home_app.ToolPage",
    ]

    @property
    def is_seasonal(self):
        return bool(self.active_from or self.active_until)

    @property
    def is_currently_active(self):
        today = timezone.now().date()
        if self.active_from and today < self.active_from:
            return False
        if self.active_until and today > self.active_until:
            return False
        return True

    @property
    def is_visible(self):
        return not self.is_seasonal or self.is_currently_active

    @property
    def category_section(self):
        """This category's section ('info_articles' or 'news'), inherited
        from the nearest ArticleIndexPage ancestor."""
        nearest_index = self.get_ancestors().type(ArticleIndexPage).specific().last()
        return nearest_index.section if nearest_index else None

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["can_edit_style"] = self.can_edit_in_editor_mode(request.user)
        context["can_sync_mirrored_page"] = self.can_sync_mirrored_page(request.user)
        context["translation_nudge"] = self.translation_nudge(request.user)
        subcategories = (
            CategoryPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
        )
        context["main_subcategories"], context["seasonal_subcategories"] = (
            _split_categories_by_season(subcategories)
        )
        context["union_categories"] = (
            StudentUnionCategoryPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
        )
        articles = ArticlePage.objects.child_of(self).filter(locale=Locale.get_active())
        context["articles"] = _articles_including_drafts_for_editor(
            articles, self, request.user
        ).order_by("-published_date")
        tools_query = (
            ToolPage.objects.descendant_of(self)
            if self.show_nested_tools
            else ToolPage.objects.child_of(self)
        )
        context["tools"] = (
            tools_query.live().filter(locale=Locale.get_active()).order_by("title")
        )
        return context


class ArticleIndexPage(
    EditorModeMixin, BannerStyleMixin, TranslationWarningMixin, Page
):  # pylint: disable=too-many-ancestors
    """Landing page listing all article categories and suggested articles."""

    template = "info_articles/pages/article_index_page.html"

    intro = RichTextField(blank=True)
    general_info = RichTextField(
        blank=True,
        help_text="Optional -- a short paragraph of general information about this section, shown below the intro.",
    )

    SECTION_CHOICES = [
        ("info_articles", "Info articles"),
        ("news", "News"),
        ("hub", "Hub (structural only, not a content section itself)"),
    ]

    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        default="info_articles",
        help_text=(
            "Which part of the site this index (and the categories under it) "
            "belongs to - used to keep e.g. news categories out of the info-articles "
            "sidemenu, and vice versa. Use 'Hub' for a purely structural index "
            "whose children are other index pages (e.g. the top-level page holding "
            "both the info-articles and news indexes)."
        ),
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("general_info"),
        FieldPanel("section"),
    ]

    subpage_types = [
        "ifi_home_app.ArticleIndexPage",
        "ifi_home_app.CategoryPage",
        "ifi_home_app.StudentUnionCategoryPage",
        "ifi_home_app.ToolPage",
        "ifi_home_app.EventIndexPage",
        "ifi_home_app.ArticlePage",  # only actually creatable when not a "hub" -- see can_create_at()
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["can_edit_style"] = self.can_edit_in_editor_mode(request.user)
        context["can_sync_mirrored_page"] = self.can_sync_mirrored_page(request.user)
        context["translation_nudge"] = self.translation_nudge(request.user)
        categories = (
            CategoryPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
        )
        context["main_categories"], context["seasonal_categories"] = (
            _split_categories_by_season(categories)
        )
        context["union_categories"] = (
            StudentUnionCategoryPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
        )
        suggested_articles = ArticlePage.objects.descendant_of(self).filter(
            locale=Locale.get_active()
        )
        context["suggested_articles"] = _articles_including_drafts_for_editor(
            suggested_articles, self, request.user
        ).order_by("-published_date")[:4]
        context["tools"] = (
            ToolPage.objects.child_of(self)
            .live()
            .filter(locale=Locale.get_active())
            .order_by("title")
        )
        return context
