# pylint: disable=C0114,C0115,C0116
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse
from wagtail.models import Locale, Page, Site
from wagtail_localize.operations import TranslationCreator
from wagtail_localize.strings import StringValue

from ifiplatform.apps.ifi_home_app.models import ArticleIndexPage
from ifiplatform.apps.ifi_home_app.translation import nudge
from ifiplatform.apps.ifi_home_app.translation.status import (
    pages_needing_translation,
    translation_status,
)

User = get_user_model()


def _fake_translate(source_locale, target_locale, strings):
    return {string: StringValue(f"[EN] {string.data}") for string in strings}


class TranslationNudgeTests(TestCase):
    """translation/status.py + translation/nudge.py -- see
    docs/claude_context/translation_nudge.md."""

    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.en, _ = Locale.objects.get_or_create(language_code="en")
        self.user = User.objects.create_superuser("admin", "a@test.com", "pw")
        self.root = Page.get_first_root_node()
        # Wagtail's own default welcome page -- it has no en copy either,
        # so it would show up as "needs translation" in every listing.
        Page.objects.filter(depth=2).delete()
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
        return page

    def _translate(self, page, complete):
        """A real wagtail-localize en translation of `page`, with every
        segment translated (`complete`) or none of them."""
        with self.captureOnCommitCallbacks(execute=True):
            TranslationCreator(self.user, [self.en]).create_translations(page)
        if complete:
            translation = page.get_translation(self.en)
            from wagtail_localize.models import (
                Translation,
            )  # pylint: disable=import-outside-toplevel

            translation_obj = Translation.objects.get(
                source__object_id=page.translation_key, target_locale=self.en
            )
            po = translation_obj.export_po()
            for entry in po:
                entry.msgstr = f"EN {entry.msgid}"
            translation_obj.import_po(po)
            with self.captureOnCommitCallbacks(execute=True):
                translation_obj.save_target(publish=True)
            return translation
        return page.get_translation(self.en)

    def test_missing_without_english_copy(self):
        self.assertEqual(translation_status(self.hub, self.user)["reason"], "missing")

    def test_missing_for_alias(self):
        self.hub.copy_for_translation(self.en, alias=True)
        self.assertEqual(translation_status(self.hub, self.user)["reason"], "missing")

    def test_outdated_for_incomplete_translation(self):
        en_page = self._translate(self.hub, complete=False)
        status = translation_status(self.hub, self.user)
        self.assertEqual(status["reason"], "outdated")
        self.assertEqual(
            status["editor_url"], reverse("wagtailadmin_pages:edit", args=[en_page.id])
        )

    def test_none_when_up_to_date(self):
        self._translate(self.hub, complete=True)
        self.assertIsNone(translation_status(self.hub, self.user))

    def test_none_for_english_pages(self):
        en_page = self._translate(self.hub, complete=False)
        self.assertIsNone(translation_status(en_page, self.user))

    def test_machine_url_needs_translator_and_permission(self):
        with patch(
            "ifi_home_app.translation.status.get_machine_translator",
            return_value=object(),
        ):
            self.assertIsNotNone(translation_status(self.hub, self.user)["machine_url"])
            editor = User.objects.create_user("editor", "e@test.com", "pw")
            self.assertIsNone(translation_status(self.hub, editor)["machine_url"])
        with patch(
            "ifi_home_app.translation.status.get_machine_translator", return_value=None
        ):
            self.assertIsNone(translation_status(self.hub, self.user)["machine_url"])

    def test_dashboard_list_only_affected_pages(self):
        self._translate(self.hub, complete=True)
        child = self._page(self.hub, "Nyheter")
        total, statuses = pages_needing_translation(self.user)
        self.assertEqual(total, 1)
        self.assertEqual(statuses[0]["page"].pk, child.pk)

    def test_after_publish_adds_warning_with_buttons(self):
        request = RequestFactory().get("/")
        request.user = self.user
        request.session = SessionStore()
        request._messages = FallbackStorage(request)  # pylint: disable=protected-access
        with patch(
            "ifi_home_app.translation.status.get_machine_translator",
            return_value=object(),
        ):
            nudge.warn_after_publish(request, self.hub)
        text = str(list(get_messages(request))[0])
        self.assertIn("missing", text)
        self.assertIn("Machine-translate now", text)
        self.assertIn("Open translation editor", text)

    def test_admin_surfaces_show_the_nudge(self):
        self.client.force_login(self.user)
        edit_html = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.hub.id])
        ).content.decode()
        self.assertIn("Open translation editor", edit_html)
        explore_html = self.client.get(
            reverse("wagtailadmin_explore", args=[self.root.id])
        ).content.decode()
        self.assertIn("Needs translation", explore_html)
        home_html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        self.assertIn("Needs English translation", home_html)

    def test_no_nudge_when_up_to_date(self):
        self._translate(self.hub, complete=True)
        self.client.force_login(self.user)
        explore_html = self.client.get(
            reverse("wagtailadmin_explore", args=[self.root.id])
        ).content.decode()
        self.assertNotIn("Needs translation", explore_html)
        home_html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        self.assertNotIn("Needs English translation", home_html)

    @patch("ifi_home_app.translation.deepl.DeepLTranslator.translate")
    def test_page_only_command_skips_children(self, mock_translate):
        mock_translate.side_effect = _fake_translate
        child = self._page(self.hub, "Nyheter")
        with self.captureOnCommitCallbacks(execute=True):
            call_command(
                "machine_translate_subtree",
                str(self.hub.id),
                str(self.user.id),
                "--page-only",
            )
        self.assertIn("[EN]", self.hub.get_translation(self.en).title)
        self.assertIsNone(child.get_translation_or_none(self.en))
