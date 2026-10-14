# pylint: disable=C0114,C0115,C0116
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Locale, Page, Site

from ifi_home_app.models import ArticleIndexPage, SegmentTranslation, WaitingForEnglish
from ifi_home_app.translation import (
    english_editor,
    nudge,
    page_segments,
    stored_translations,
)
from ifi_home_app.translation.english_overlay import english
from ifi_home_app.translation.status import (
    page_needs_translation,
    pages_needing_translation,
    translation_status,
)

User = get_user_model()


class TranslationNudgeTests(TestCase):
    """translation/status.py + translation/nudge.py -- see
    docs/claude_context/translation_nudge.md."""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.user = User.objects.create_superuser("admin", "a@test.com", "pw")
        self.root = Page.get_first_root_node()
        Page.objects.filter(depth=2).delete()  # Wagtail's default welcome page
        self.hub = self._page(self.root, "Artikler")
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": "localhost", "root_page": self.hub},
        )

    def _page(self, parent, title):
        page = ArticleIndexPage(
            locale=self.nb, title=title, slug=title.lower(), section="hub"
        )
        parent.add_child(instance=page)
        page.save_revision().publish()
        return Page.objects.get(pk=page.pk).specific

    def _english(self, page):
        stored_translations.save_machine(
            page,
            {s: f"EN {s.norwegian_text}" for s in page_segments.extract_segments(page)},
        )

    def _waiting(self, page, minutes_ago):
        content_type_id, object_id = stored_translations.object_key(page)
        WaitingForEnglish.objects.create(
            content_type_id=content_type_id,
            object_id=object_id,
            requested_at=timezone.now() - timedelta(minutes=minutes_ago),
        )

    def test_missing_without_english(self):
        status = translation_status(self.hub, self.user)
        self.assertEqual(status["reason"], "missing")
        self.assertEqual(status["editor_url"], english_editor.editor_url(self.hub))
        self.assertIsNone(status["machine_url"])

    def test_outdated_after_norwegian_changes(self):
        self._english(self.hub)
        self.hub.title = "Artikler og nyheter"
        self.hub.save_revision().publish()
        status = translation_status(
            Page.objects.get(pk=self.hub.pk).specific, self.user
        )
        self.assertEqual(status["reason"], "outdated")

    def test_none_when_complete_or_on_its_way(self):
        self._english(self.hub)
        self.assertIsNone(translation_status(self.hub, self.user))
        child = self._page(self.hub, "Nyheter")
        self._waiting(child, minutes_ago=1)
        self.assertIsNone(translation_status(child, self.user))

    def test_dashboard_lists_stuck_and_failed_pages_only(self):
        self._page(self.hub, "Uoversatt")  # missing, but not stuck: not listed
        stuck = self._page(self.hub, "Stuck")
        self._waiting(stuck, minutes_ago=30)
        failed = self._page(self.hub, "Failed")
        self._english(failed)
        SegmentTranslation.objects.filter(norwegian_text="Failed").update(
            has_error=True
        )
        total, statuses = pages_needing_translation(self.user)
        self.assertEqual(total, 2)
        self.assertEqual({s["page"].pk for s in statuses}, {stuck.pk, failed.pk})

    def test_visitor_banner_one_rule(self):
        complete = self._page(self.hub, "Komplett")
        self._english(complete)
        waiting = self._page(self.hub, "Venter")
        self._waiting(waiting, minutes_ago=1)
        self.assertFalse(page_needs_translation(self.hub))  # Norwegian shown
        with english():  # nothing may be saved in here (write blocker)
            self.assertTrue(page_needs_translation(self.hub))
            self.assertFalse(page_needs_translation(Page.objects.get(pk=complete.pk)))
            self.assertFalse(page_needs_translation(waiting))

    def test_after_publish_adds_warning_with_editor_button(self):
        request = RequestFactory().get("/")
        request.user = self.user
        request.session = SessionStore()
        request._messages = FallbackStorage(request)  # pylint: disable=protected-access
        nudge.warn_after_publish(request, self.hub)
        text = str(list(get_messages(request))[0])
        self.assertIn("missing", text)
        self.assertIn("Open English editor", text)

    def test_admin_surfaces_show_the_nudge(self):
        stuck = self._page(self.hub, "Stuck")
        self._waiting(stuck, minutes_ago=30)
        self.client.force_login(self.user)
        edit_html = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.hub.id])
        ).content.decode()
        self.assertIn("Open English editor", edit_html)
        explore_html = self.client.get(
            reverse("wagtailadmin_explore", args=[self.root.id])
        ).content.decode()
        self.assertIn("Needs translation", explore_html)
        home_html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        self.assertIn("Needs English translation", home_html)

    def test_no_nudge_when_complete(self):
        self._english(self.hub)
        self.client.force_login(self.user)
        explore_html = self.client.get(
            reverse("wagtailadmin_explore", args=[self.root.id])
        ).content.decode()
        self.assertNotIn("Needs translation", explore_html)
        home_html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        self.assertNotIn("Needs English translation", home_html)
        self.assertIn("All English is up to date", home_html)

    def test_wagtail_localize_ui_is_gone(self):
        self.client.force_login(self.user)
        home_html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        edit_html = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.hub.id])
        ).content.decode()
        for html in (home_html, edit_html):
            self.assertNotIn(
                "wagtail-localize", html.lower().replace("_", "-").split("<script")[0]
            )
            self.assertNotIn("Translate this page", html)
            self.assertNotIn("Sync translated pages", html)
        self.assertNotIn(">Translations<", home_html)
        self.assertNotIn(">Locales<", home_html)
