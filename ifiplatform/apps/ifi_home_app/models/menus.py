"""Editor-curated navigation: MenuGroups (titled, ordered link lists) arranged
into the three Menus (sidemenu, home dropmenus, homepage shortcuts).

Design rationale: docs/claude_context/menus.md"""

from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable, Page, TranslatableMixin
from wagtail.snippets.models import register_snippet

from .article.pages import CategoryPage

MENU_KEYS = [
    ("sidemenu", "Sidemenu"),
    ("home_dropmenu", "Home dropmenus"),
    ("shortcuts", "Homepage shortcuts"),
]

# Inline SVGs in home/partials/shortcuts/shortcut_icon.html -- blank keeps the
# generic menu icon.
SHORTCUT_ICONS = [
    ("info", "Info"),
    ("news", "News"),
    ("unions", "Student unions"),
    ("jobs", "Jobs"),
    ("events", "Events"),
    ("tools", "Tools"),
]

# Checked in order for a link's thumbnail (UnionPage.logo, ToolPage.image,
# ArticlePage.hero_image, ...).
THUMBNAIL_FIELDS = ("logo", "image", "hero_image")


class MenuGroup(TranslatableMixin, ClusterableModel):
    """A titled, ordered list of links, placed into one or more Menus.
    Registered as a snippet in wagtail_hooks.py (Norwegian-first listing)."""

    title = models.CharField(max_length=100)
    short_title = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional -- shown instead of the title on narrow screens.",
    )
    link_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text='Where the group\'s heading and its "All" link go.',
    )
    link_url = models.URLField(
        blank=True,
        help_text="An external address for the heading instead of a page.",
    )
    icon = models.CharField(
        max_length=20,
        blank=True,
        choices=SHORTCUT_ICONS,
        help_text="Shown on the group's homepage shortcut card. Blank uses the plain menu icon.",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("short_title"),
        FieldPanel("icon"),
        MultiFieldPanel(
            [FieldPanel("link_page"), FieldPanel("link_url")],
            heading="Heading link (optional, pick at most one)",
        ),
        InlinePanel("links", label="Links"),
    ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_ifi_home_app_menugroup",
            )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.link_page and self.link_url:
            raise ValidationError(
                "Pick either a page or an external address for the heading, not both."
            )


class MenuGroupLink(TranslatableMixin, Orderable):
    """One link in a MenuGroup: a page on the site or an external address."""

    group = ParentalKey(MenuGroup, on_delete=models.CASCADE, related_name="links")
    label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Leave blank to use the page's own title.",
    )
    page = models.ForeignKey(
        Page, null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    url = models.URLField(
        blank=True, help_text="An external address instead of a page."
    )
    description = models.CharField(max_length=100, blank=True)
    prefix = models.CharField(
        max_length=50,
        blank=True,
        help_text='Optional non-bold text before the label, e.g. "Listings at".',
    )

    panels = [
        FieldPanel("label"),
        FieldPanel("page"),
        FieldPanel("url"),
        FieldPanel("description"),
        FieldPanel("prefix"),
    ]

    class Meta(Orderable.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_ifi_home_app_menugrouplink",
            )
        ]

    def clean(self):
        super().clean()
        if bool(self.page) == bool(self.url):
            raise ValidationError("Pick either a page or an external address.")


@register_snippet
class Menu(ClusterableModel):
    """One of the site's menus, listing MenuGroups in order. Shared by every
    language -- each group is shown in the visitor's language."""

    key = models.CharField(max_length=20, choices=MENU_KEYS, unique=True)

    panels = [FieldPanel("key"), InlinePanel("slots", label="Groups")]

    def __str__(self):
        return self.get_key_display()


class MenuSlot(Orderable):
    """A MenuGroup's place in a Menu."""

    menu = ParentalKey(Menu, on_delete=models.CASCADE, related_name="slots")
    group = models.ForeignKey(MenuGroup, on_delete=models.CASCADE, related_name="+")
    column = models.PositiveSmallIntegerField(
        default=1, help_text="Homepage shortcuts only: which column the group goes in."
    )
    hide_on_mobile = models.BooleanField(
        default=False,
        help_text="Home dropmenus only: hide on narrow screens, e.g. when the sidemenu already has it.",
    )

    panels = [FieldPanel("group"), FieldPanel("column"), FieldPanel("hide_on_mobile")]


def _thumbnail(page):
    for field in THUMBNAIL_FIELDS:
        image = getattr(page, field, None)
        if image:
            return image
    return None


def _resolve_page(page):
    """The live, visible version of `page` in the active locale, or None."""
    if page is None:
        return None
    page = page.specific.localized
    if not page.live:
        return None
    if isinstance(page, CategoryPage) and not page.is_visible:
        return None
    return page


def _resolve_link(link):
    if link.url:
        return {
            "label": link.label or link.url,
            "url": link.url,
            "external": True,
            "description": link.description,
            "prefix": link.prefix,
            "image": None,
        }
    page = _resolve_page(link.page)
    if page is None:
        return None
    return {
        "label": link.label or page.title,
        "url": page.url,
        "external": False,
        "description": link.description,
        "prefix": link.prefix,
        "image": _thumbnail(page),
    }


def _resolve_group(slot):
    group = slot.group.localized
    link_page = _resolve_page(group.link_page)
    links = [
        link for link in (_resolve_link(link) for link in group.links.all()) if link
    ]
    url = link_page.url if link_page else group.link_url
    return {
        "title": group.title,
        "short_title": group.short_title,
        "icon": slot.group.icon or group.icon,
        "url": url,
        "external": bool(group.link_url) and not link_page,
        # an "All" link to the heading's own target, unless a link already goes there
        "show_all": bool(url) and all(link["url"] != url for link in links),
        "hide_on_mobile": slot.hide_on_mobile,
        "column": slot.column,
        "links": links,
    }


def get_menu(key):
    """The Menu with this key, resolved to plain dicts for the active locale:
    one per group, in order. Empty if the menu hasn't been set up."""
    menu = Menu.objects.filter(key=key).first()
    if menu is None:
        return []
    slots = menu.slots.select_related("group").all()
    return [_resolve_group(slot) for slot in slots]
