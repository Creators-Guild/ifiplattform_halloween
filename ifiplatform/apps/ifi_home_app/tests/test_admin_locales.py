# pylint: disable=C0114,C0115,C0116
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse
from wagtail.models import Locale, Page
from wagtail_localize.models import Translation

from ifiplatform.apps.ifi_home_app.models import ArticleIndexPage
from ifiplatform.apps.ifi_home_app.models.menus import MenuGroup, MenuGroupLink
from ifiplatform.apps.ifi_home_app.translation import admin_locales
from ifiplatform.apps.ifi_home_app.translation.snippets import link_existing_translation

User = get_user_model()


class AdminLocaleTests(TestCase):
    """translation/admin_locales.py -- see docs/claude_context/admin_locales.md."""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.en, _ = Locale.objects.get_or_create(language_code="en")
        self.root = Page.get_first_root_node()
        self.nb_index = ArticleIndexPage(
            locale=self.nb, title="Artikler", slug="artikler", section="hub"
        )
        self.root.add_child(instance=self.nb_index)
        self.nb_index.save_revision().publish()
        self.en_index = self.nb_index.copy_for_translation(self.en)
        self.en_index.save_revision().publish()
        self.en_child = ArticleIndexPage(
            locale=self.en, title="Child", slug="child", section="news"
        )
        self.en_index.add_child(instance=self.en_child)

        self.superuser = User.objects.create_superuser("admin", "a@test.com", "pw")
        self.editor = User.objects.create_user("editor", "e@test.com", "pw")

    def _request(self, user, show_all=False):
        request = RequestFactory().get("/")
        request.user = user
        request.session = SessionStore()
        if show_all:
            request.session[admin_locales.SESSION_KEY] = True
        return request

    def _root_children(self, request):
        """The indexes left at the root -- ignoring Wagtail's own default
        welcome page, which also lives there."""
        pages = admin_locales.filter_explorer_pages(
            self.root, self.root.get_children(), request
        )
        return set(
            pages.filter(pk__in=[self.nb_index.pk, self.en_index.pk]).values_list(
                "pk", flat=True
            )
        )

    def test_explorer_root_hides_english(self):
        self.assertEqual(
            self._root_children(self._request(self.editor)), {self.nb_index.pk}
        )

    def test_english_parent_still_lists_its_english_children(self):
        pages = admin_locales.filter_explorer_pages(
            self.en_index, self.en_index.get_children(), self._request(self.editor)
        )
        self.assertEqual(list(pages), [self.en_child.page_ptr])

    def test_chooser_is_norwegian_only(self):
        pages = admin_locales.filter_chooser_pages(
            Page.objects.filter(depth__gt=1), self._request(self.editor)
        )
        self.assertEqual({page.locale_id for page in pages}, {self.nb.id})

    def test_superuser_toggle_shows_english(self):
        self.assertEqual(
            self._root_children(self._request(self.superuser, show_all=True)),
            {self.nb_index.pk, self.en_index.pk},
        )

    def test_toggle_is_ignored_for_non_superusers(self):
        self.assertEqual(
            self._root_children(self._request(self.editor, show_all=True)),
            {self.nb_index.pk},
        )

    def test_toggle_view_flips_session_flag(self):
        request = self._request(self.superuser)
        admin_locales.toggle_all_locales(request)
        self.assertTrue(request.session[admin_locales.SESSION_KEY])
        admin_locales.toggle_all_locales(request)
        self.assertFalse(request.session[admin_locales.SESSION_KEY])

    def test_toggle_view_rejects_non_superusers(self):
        with self.assertRaises(PermissionDenied):
            admin_locales.toggle_all_locales(self._request(self.editor))


class LinkExistingTranslationTests(TestCase):
    """translation/snippets.py"""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.en, _ = Locale.objects.get_or_create(language_code="en")

    def test_keeps_english_text_and_registers_translation(self):
        nb_group = MenuGroup(locale=self.nb, title="Nyheter")
        nb_group.links.add(
            MenuGroupLink(
                sort_order=0, url="https://example.com", label="Lenke", prefix="Hos"
            )
        )
        nb_group.save()
        en_group = nb_group.copy_for_translation(self.en)
        en_group.title = "News"
        link = en_group.links.all()[0]
        link.label, link.prefix = "Link", "At"
        en_group.save()

        translation = link_existing_translation(nb_group, en_group)
        link_existing_translation(nb_group, en_group)

        self.assertEqual(Translation.objects.filter(pk=translation.pk).count(), 1)
        en_group = MenuGroup.objects.get(
            translation_key=nb_group.translation_key, locale=self.en
        )
        self.assertEqual(en_group.title, "News")
        self.assertEqual(
            MenuGroup.objects.filter(translation_key=nb_group.translation_key).count(),
            2,
        )
        en_link = en_group.links.get()
        self.assertEqual(
            (en_link.label, en_link.prefix, en_link.url),
            ("Link", "At", "https://example.com"),
        )


class NorwegianFirstSnippetTests(TestCase):
    """The snippet listing and chooser default to nb (admin_locales.py)."""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.en, _ = Locale.objects.get_or_create(language_code="en")
        nb_group = MenuGroup.objects.create(locale=self.nb, title="Norsk gruppe")
        en_group = nb_group.copy_for_translation(self.en)
        en_group.title = "English group"
        en_group.save()
        self.superuser = User.objects.create_superuser("admin", "a@test.com", "pw")
        self.client.force_login(self.superuser)

    def _get(self, url_name, **params):
        return self.client.get(reverse(url_name), params).content.decode()

    def test_listing_defaults_to_norwegian(self):
        html = self._get("wagtailsnippets_ifi_home_app_menugroup:list")
        self.assertIn("Norsk gruppe", html)
        self.assertNotIn("English group", html)

    def test_listing_can_still_pick_english(self):
        html = self._get("wagtailsnippets_ifi_home_app_menugroup:list", locale="en")
        self.assertIn("English group", html)
        self.assertNotIn("Norsk gruppe", html)

    def test_chooser_defaults_to_norwegian(self):
        html = self._get("wagtailsnippetchoosers_ifi_home_app_menugroup:choose_results")
        self.assertIn("Norsk gruppe", html)
        self.assertNotIn("English group", html)

    def test_superuser_toggle_shows_all(self):
        session = self.client.session
        session[admin_locales.SESSION_KEY] = True
        session.save()
        html = self._get("wagtailsnippets_ifi_home_app_menugroup:list")
        self.assertIn("Norsk gruppe", html)
        self.assertIn("English group", html)
