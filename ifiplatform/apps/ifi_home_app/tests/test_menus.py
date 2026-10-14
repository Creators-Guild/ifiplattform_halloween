# pylint: disable=C0114,C0115,C0116
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone, translation
from wagtail.models import Locale, Page, Site

from ifi_home_app.models import ArticleIndexPage
from ifi_home_app.models.article_models import CategoryPage
from ifi_home_app.models.menus import (
    SHORTCUT_ICONS,
    Menu,
    MenuGroup,
    MenuGroupLink,
    MenuSlot,
    get_menu,
)
from ifi_home_app.templatetags.article_tags import get_shortcut_columns
from ifi_home_app.translation import page_segments, stored_translations
from ifi_home_app.translation.english_overlay import english


class MenuTests(TestCase):
    """models/menus.py -- see docs/claude_context/menus.md."""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.index = ArticleIndexPage(
            locale=self.nb, title="Artikler", slug="artikler", section="info_articles"
        )
        Page.get_first_root_node().add_child(instance=self.index)
        self.index.save_revision().publish()

    def _category(self, title, **kwargs):
        category = CategoryPage(
            locale=self.nb, title=title, slug=title.lower(), **kwargs
        )
        self.index.add_child(instance=category)
        category.save_revision().publish()
        return category

    def _group(self, title="Gruppe", links=(), **kwargs):
        group = MenuGroup(locale=self.nb, title=title, **kwargs)
        for order, link in enumerate(links):
            group.links.add(MenuGroupLink(sort_order=order, **link))
        group.save()
        return group

    def _menu(self, key, *slots):
        menu = Menu(key=key)
        for order, slot in enumerate(slots):
            slot = slot if isinstance(slot, dict) else {"group": slot}
            menu.slots.add(MenuSlot(sort_order=order, **slot))
        menu.save()
        return menu

    def _nb(self, key):
        with translation.override("nb"):
            return get_menu(key)

    def test_missing_menu_is_empty(self):
        self.assertEqual(self._nb("sidemenu"), [])

    def test_keeps_editor_order(self):
        first, second = self._category("Første"), self._category("Andre")
        group = self._group(links=[{"page": second}, {"page": first}])
        self._menu("sidemenu", self._group("B"), group)

        menu = self._nb("sidemenu")
        self.assertEqual([g["title"] for g in menu], ["B", "Gruppe"])
        self.assertEqual(
            [link["label"] for link in menu[1]["links"]], ["Andre", "Første"]
        )

    def test_skips_unpublished_and_off_season_pages(self):
        visible = self._category("Synlig")
        unpublished = self._category("Upublisert")
        unpublished.unpublish()
        off_season = self._category(
            "Sesong", active_until=timezone.now().date() - timedelta(days=1)
        )
        self._menu(
            "sidemenu",
            self._group(
                links=[{"page": visible}, {"page": unpublished}, {"page": off_season}]
            ),
        )

        self.assertEqual(
            [link["label"] for link in self._nb("sidemenu")[0]["links"]], ["Synlig"]
        )

    def test_external_links_are_flagged(self):
        self._menu(
            "sidemenu",
            self._group(
                link_url="https://example.com/heading",
                links=[{"url": "https://example.com", "label": "Eksempel"}],
            ),
        )

        group = self._nb("sidemenu")[0]
        self.assertTrue(group["external"])
        self.assertEqual(group["url"], "https://example.com/heading")
        self.assertTrue(group["links"][0]["external"])

    def test_heading_page_link_is_internal(self):
        self._menu("sidemenu", self._group(link_page=self.index))

        group = self._nb("sidemenu")[0]
        self.assertFalse(group["external"])
        self.assertEqual(group["url"], self.index.url)

    def test_group_rejects_both_heading_links(self):
        group = MenuGroup(
            locale=self.nb,
            title="Begge",
            link_page=self.index,
            link_url="https://example.com",
        )
        with self.assertRaises(ValidationError):
            group.clean()

    def test_link_needs_exactly_one_target(self):
        with self.assertRaises(ValidationError):
            MenuGroupLink(label="Ingen").clean()
        with self.assertRaises(ValidationError):
            MenuGroupLink(page=self.index, url="https://example.com").clean()

    def _english(self, obj, english_by_norwegian):
        stored_translations.save_machine(
            obj,
            {
                segment: english_by_norwegian[segment.norwegian_text]
                for segment in page_segments.extract_segments(obj)
                if segment.norwegian_text in english_by_norwegian
            },
        )

    def test_blank_label_uses_english_page_title(self):
        category = self._category("Akademisk")
        self._english(category, {"Akademisk": "Academic"})
        self._menu("sidemenu", self._group(links=[{"page": category}]))

        with translation.override("en"), english():
            link = get_menu("sidemenu")[0]["links"][0]
            expected_url = category.url
        self.assertEqual(link["label"], "Academic")
        self.assertEqual(link["url"], expected_url)

    def test_en_falls_back_to_untranslated_nb_group(self):
        self._menu("sidemenu", self._group("Bare norsk"))

        with translation.override("en"), english():
            self.assertEqual(get_menu("sidemenu")[0]["title"], "Bare norsk")

    def test_en_uses_english_group_title(self):
        group = self._group("Nyheter")
        self._english(group, {"Nyheter": "News"})
        self._menu("sidemenu", group)

        with translation.override("en"), english():
            self.assertEqual(get_menu("sidemenu")[0]["title"], "News")
        self.assertEqual(self._nb("sidemenu")[0]["title"], "Nyheter")

    def test_shortcuts_are_grouped_by_column(self):
        self._menu(
            "shortcuts",
            {"group": self._group("A"), "column": 2},
            {"group": self._group("B"), "column": 1},
            {"group": self._group("C"), "column": 2},
        )

        with translation.override("nb"):
            columns = get_shortcut_columns()
        self.assertEqual(
            [[g["title"] for g in column] for column in columns], [["B"], ["A", "C"]]
        )

    def test_icon_also_shows_in_english(self):
        self._menu("shortcuts", self._group("Nyheter", icon="news"))

        with translation.override("en"), english():
            self.assertEqual(get_menu("shortcuts")[0]["icon"], "news")

    def test_shortcut_icon_partial(self):
        from django.template.loader import (
            render_to_string,
        )  # pylint: disable=import-outside-toplevel

        for icon, _label in SHORTCUT_ICONS:
            self.assertIn(
                "<svg",
                render_to_string(
                    "home/partials/shortcuts/shortcut_icon.html", {"icon": icon}
                ),
            )
        self.assertIn(
            "black_menu_icon",
            render_to_string(
                "home/partials/shortcuts/shortcut_icon.html", {"icon": ""}
            ),
        )

    def test_show_all_unless_a_link_already_goes_there(self):
        # pages only have a URL once they're under a Site
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": "localhost", "root_page": self.index},
        )
        other = self._category("Annen")
        self._menu(
            "sidemenu",
            self._group(
                "Med egen Alle",
                link_page=self.index,
                links=[{"page": self.index, "label": "Alle"}],
            ),
            self._group("Uten", link_page=self.index, links=[{"page": other}]),
            self._group("Uten lenke"),
        )

        self.assertEqual(
            [g["show_all"] for g in self._nb("sidemenu")], [False, True, False]
        )
