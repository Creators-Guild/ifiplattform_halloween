# pylint: disable=C0114,C0115,C0116
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from wagtail.models import Locale, Page
from wagtail_localize.strings import StringValue

from ifiplatform.apps.ifi_home_app.models import ArticleIndexPage

User = get_user_model()


def _make_page(nb_locale, **kwargs):
    root = Page.get_first_root_node()
    kwargs.setdefault("title", "Smoke Test Page")
    kwargs.setdefault("slug", "smoke-test-page")
    kwargs.setdefault("section", "hub")
    page = ArticleIndexPage(locale=nb_locale, **kwargs)
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def _fake_translate(source_locale, target_locale, strings):
    return {string: StringValue(f"[EN] {string.data}") for string in strings}


class MachineTranslateSubtreeCommandTests(TestCase):
    """The machine_translate_subtree management command -- the real
    implementation behind translation/views.py's background-process
    launch. See docs/claude_context/translation_views.md."""

    def setUp(self):
        self.nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
        Locale.objects.get_or_create(language_code="en")
        self.user = User.objects.create_superuser("translator", "t@test.com", "pw")

    @patch("ifi_home_app.translation.deepl.DeepLTranslator.translate")
    def test_translates_and_publishes(self, mock_translate):
        mock_translate.side_effect = _fake_translate
        page = _make_page(self.nb_locale)

        # save_target() defers the actual .publish() via
        # transaction.on_commit() -- TestCase wraps each test in a
        # transaction that's rolled back, not committed, so those callbacks
        # are silently discarded unless captured like this.
        with self.captureOnCommitCallbacks(execute=True):
            call_command("machine_translate_subtree", str(page.id), str(self.user.id))

        translation = page.get_translation(Locale.objects.get(language_code="en"))
        self.assertTrue(translation.live)
        self.assertIn("[EN]", translation.title)

    @patch("ifi_home_app.translation.deepl.DeepLTranslator.translate")
    def test_one_page_failure_does_not_abort_the_rest(self, mock_translate):
        """A subtree of 2 pages -- the child fails, the parent must still
        succeed (previously, one @transaction.atomic around the whole
        batch meant a single failure rolled back everything)."""
        parent = _make_page(self.nb_locale, title="Parent", slug="parent")
        child = ArticleIndexPage(
            locale=self.nb_locale, title="Child", slug="child", section="hub"
        )
        parent.add_child(instance=child)
        child.save_revision().publish()

        def fail_on_child(source_locale, target_locale, strings):
            if any("Child" in s.data for s in strings):
                raise ConnectionError("simulated DeepL outage")
            return _fake_translate(source_locale, target_locale, strings)

        mock_translate.side_effect = fail_on_child

        with self.captureOnCommitCallbacks(execute=True):
            call_command("machine_translate_subtree", str(parent.id), str(self.user.id))

        en_locale = Locale.objects.get(language_code="en")
        parent_translation = parent.get_translation(en_locale)
        self.assertTrue(parent_translation.live)
        self.assertIn("[EN]", parent_translation.title)
        # TranslationCreator.create_translations() eagerly creates an empty
        # draft translation for every page in the subtree up front (same
        # as wagtail-localize's own plain "Translate" button), copying
        # `live` from the nb source as part of that copy -- so `.live`
        # alone isn't a signal that real translated content ever landed.
        # The title is: still the original nb title (never touched by
        # save_target()) confirms the child's failed DeepL call really did
        # leave it untranslated, not just unpublished.
        child_translation = child.get_translation_or_none(en_locale)
        self.assertIsNotNone(child_translation)
        self.assertEqual(child_translation.title, "Child")

    @patch("ifi_home_app.translation.deepl.DeepLTranslator.translate")
    def test_rerun_after_partial_failure_only_retries_failed_pages(
        self, mock_translate
    ):
        """Resumability, verified directly: re-running after a partial
        failure must cost zero extra DeepL calls for the page that already
        succeeded, and must translate the one that previously failed."""
        parent = _make_page(self.nb_locale, title="Parent", slug="parent")
        child = ArticleIndexPage(
            locale=self.nb_locale, title="Child", slug="child", section="hub"
        )
        parent.add_child(instance=child)
        child.save_revision().publish()

        should_fail = {"child": True}

        def fail_on_child_once(source_locale, target_locale, strings):
            if any("Child" in s.data for s in strings) and should_fail["child"]:
                raise ConnectionError("simulated DeepL outage")
            return _fake_translate(source_locale, target_locale, strings)

        mock_translate.side_effect = fail_on_child_once
        with self.captureOnCommitCallbacks(execute=True):
            call_command("machine_translate_subtree", str(parent.id), str(self.user.id))
        self.assertEqual(
            mock_translate.call_count, 2
        )  # parent ok, child attempted+failed

        should_fail["child"] = False
        with self.captureOnCommitCallbacks(execute=True):
            call_command("machine_translate_subtree", str(parent.id), str(self.user.id))
        # Only the child should have been retried -- the parent's segment
        # already has a StringTranslation, so apply_machine_translation()
        # skips it and translate() is never called for it again.
        self.assertEqual(mock_translate.call_count, 3)

        en_locale = Locale.objects.get(language_code="en")
        self.assertTrue(child.get_translation(en_locale).live)
