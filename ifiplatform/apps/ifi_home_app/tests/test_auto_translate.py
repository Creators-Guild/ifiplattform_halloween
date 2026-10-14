# pylint: disable=C0114,C0115,C0116
"""DeepL client, automatic translation (waiting table, every-minute and
nightly runs), the English editor and the read-only list -- see
docs/claude_context/translation_overlay.md."""

from datetime import timedelta
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Locale, Page

from ifi_home_app.models import (
    ArticleIndexPage,
    ArticlePage,
    EnglishSlug,
    GlossarySyncState,
    MenuGroup,
    MenuGroupLink,
    SegmentTranslation,
    TranslationSettings,
    WaitingForEnglish,
)
from ifi_home_app.translation import (
    auto_translate,
    deepl,
    english_editor,
    page_segments,
    stored_translations,
)
from ifi_home_app.translation.english_overlay import english


def fake_deepl(texts):
    """'English' = the Norwegian with EN: in front (tags kept)."""
    return [f"EN: {text}" for text in texts]


class AutoTranslateTestCase(TestCase):
    def setUp(self):
        self.enterContext(
            mock.patch.object(deepl, "translate_texts", side_effect=fake_deepl)
        )
        self.enterContext(mock.patch.object(deepl, "DEEPL_CALL_DELAY_SECONDS", 0))
        self.enterContext(override_settings(DEEPL_API_KEY="test-key"))
        self.deepl = deepl.translate_texts
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.index = ArticleIndexPage(
            locale=self.nb, title="Artikler", slug="artikler", section="info_articles"
        )
        Page.get_first_root_node().add_child(instance=self.index)
        self.index.save_revision().publish()
        WaitingForEnglish.objects.all().delete()  # start each test with nothing waiting

    def article(self, title="Fadderuke", slug="fadderuke", publish=True):
        page = ArticlePage(
            locale=self.nb,
            title=title,
            slug=slug,
            published_date=timezone.now().date(),
            intro="<p>Velkommen til Ifi.</p>",
            body=[("heading", {"text": "Program", "level": "h2"})],
        )
        self.index.add_child(instance=page)
        revision = page.save_revision()
        if publish:
            revision.publish()
        return ArticlePage.objects.get(pk=page.pk)

    def waiting(self):
        return WaitingForEnglish.objects.count()


class DeepLClientTests(TestCase):
    @override_settings(DEEPL_API_KEY="abc:fx", DEEPL_GLOSSARY_ID="glossary-1")
    def test_batches_free_endpoint_glossary_and_errors(self):
        calls = []

        def post(url, data, timeout, headers):
            calls.append((url, data))
            response = requests.Response()
            response.status_code = 200
            response._content = (
                '{"translations": [%s]}'
                % ",".join('{"text": "x"}' for _ in data["text"])
            ).encode()
            return response

        with mock.patch.object(deepl.requests, "post", side_effect=post):
            english = deepl.translate_texts([f"tekst {n}" for n in range(60)])
        self.assertEqual(len(english), 60)
        self.assertEqual([len(data["text"]) for _, data in calls], [50, 10])
        self.assertEqual(calls[0][0], "https://api-free.deepl.com/v2/translate")
        self.assertEqual(calls[0][1]["glossary_id"], "glossary-1")
        self.assertEqual(calls[0][1]["tag_handling"], "xml")

        def fail(*args, **kwargs):
            response = requests.Response()
            response.status_code = 456  # DeepL: quota exceeded
            return response

        with mock.patch.object(deepl.requests, "post", side_effect=fail):
            with self.assertRaisesMessage(requests.HTTPError, "quota is used up"):
                deepl.translate_texts(["tekst"])

        def glossary_gone(*args, **kwargs):
            response = requests.Response()
            response.status_code = 404
            response._content = b'{"message": "Not found"}'
            return response

        with mock.patch.object(deepl.requests, "post", side_effect=glossary_gone):
            with self.assertRaisesMessage(requests.HTTPError, "DEEPL_GLOSSARY_ID"):
                deepl.translate_texts(["tekst"])


class WaitingTests(AutoTranslateTestCase):
    def test_publish_marks_waiting_draft_does_not(self):
        self.article(publish=False)
        self.assertEqual(self.waiting(), 0)
        page = self.article("Arrangementer", "arrangementer")
        self.assertTrue(auto_translate.is_waiting(page))

    def test_no_key_and_setting_off_do_nothing(self):
        with override_settings(DEEPL_API_KEY=""):
            self.article("Uten nøkkel", "uten-nokkel")
        settings = TranslationSettings.load()
        settings.auto_translate = False
        settings.save()
        self.article("Av", "av")
        self.assertEqual(self.waiting(), 0)

    def test_snippet_save_marks_waiting(self):
        group = MenuGroup(locale=self.nb, title="Studentliv")
        group.save()
        self.assertTrue(auto_translate.is_waiting(group))


class TranslateWaitingTests(AutoTranslateTestCase):
    def test_translates_deletes_row_and_sets_slug_once(self):
        page = self.article()
        self.assertEqual(auto_translate.translate_waiting(), (1, 0))
        self.assertEqual(self.waiting(), 0)
        with english():
            self.assertEqual(ArticlePage.objects.get(pk=page.pk).title, "EN: Fadderuke")
        self.assertEqual(EnglishSlug.objects.get(page=page).slug, "en-fadderuke")

        page.title = "Fadderuka"
        page.save_revision().publish()
        auto_translate.translate_waiting()
        self.assertEqual(EnglishSlug.objects.get(page=page).slug, "en-fadderuke")

    def test_only_changed_pieces_go_to_deepl(self):
        page = self.article()
        auto_translate.translate_waiting()
        page.title = "Fadderuka"
        page.save_revision().publish()
        self.deepl.reset_mock()
        auto_translate.translate_waiting()
        self.deepl.assert_called_once_with(["Fadderuka"])

    def test_person_fix_wins(self):
        page = self.article()
        segment = page_segments.Segment("title", "Fadderuke")
        stored_translations.save_human(page, segment, "Buddy week", None)
        auto_translate.translate_waiting()
        self.assertEqual(
            SegmentTranslation.objects.get(segment_path="title").english_text,
            "Buddy week",
        )

    def test_failure_recorded_and_retried_after_a_wait(self):
        self.article()
        self.deepl.side_effect = requests.HTTPError("456 quota exceeded")
        self.assertEqual(auto_translate.translate_waiting(), (0, 1))
        row = WaitingForEnglish.objects.get()
        self.assertEqual(row.attempts, 1)
        self.assertIn("quota", row.last_error)

        self.deepl.side_effect = fake_deepl
        self.assertEqual(auto_translate.translate_waiting(), (0, 0))  # still waiting
        WaitingForEnglish.objects.update(
            last_attempt_at=timezone.now() - timedelta(minutes=3)
        )
        self.assertEqual(auto_translate.translate_waiting(), (1, 0))

    def test_bad_output_stored_as_error_and_retried(self):
        page = self.article()
        self.deepl.side_effect = lambda texts: ['<a id="a9">x</a>' for _ in texts]
        auto_translate.translate_waiting()
        self.assertTrue(SegmentTranslation.objects.filter(has_error=True).exists())
        with english():
            self.assertEqual(ArticlePage.objects.get(pk=page.pk).title, "Fadderuke")
        self.deepl.side_effect = fake_deepl
        auto_translate.fill_missing(ArticlePage.objects.get(pk=page.pk))
        self.assertFalse(SegmentTranslation.objects.filter(has_error=True).exists())

    def test_unpublished_or_deleted_objects_are_dropped(self):
        page = self.article()
        page.unpublish()
        auto_translate.translate_waiting()
        self.assertEqual(self.waiting(), 0)
        self.deepl.assert_not_called()


class NightlyTests(AutoTranslateTestCase):
    def test_catches_up_and_cleans_up(self):
        page = self.article()
        WaitingForEnglish.objects.all().delete()  # e.g. missed while off
        summary = auto_translate.nightly()
        self.assertGreaterEqual(summary["marked waiting"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertFalse(
            stored_translations.missing_segments(ArticlePage.objects.get(pk=page.pk))
        )

    def test_glossary_update_redoes_affected_rows(self):
        self.article()
        auto_translate.translate_waiting()
        GlossarySyncState.touch()  # the glossary changed after these rows
        with mock.patch(
            "ifi_home_app.translation.glossary_terms.GLOSSARY_TERMS",
            {"Fadderuke": "Buddy week"},
        ):
            summary = auto_translate.nightly()
        self.assertEqual(summary["stale glossary rows"], 1)

    def test_setting_off_only_cleans_up(self):
        settings = TranslationSettings.load()
        settings.auto_translate = False
        settings.save()
        self.assertEqual(set(auto_translate.nightly()), {"rows cleaned up"})

    def test_command_is_quiet_with_nothing_to_do(self):
        with mock.patch("sys.stdout") as stdout:
            call_command("translate_english")
        stdout.write.assert_not_called()


class EnglishEditorTests(AutoTranslateTestCase):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser(
            "admin", "a@example.com", "pw"
        )
        self.client.force_login(self.admin)
        self.page = self.article()
        self.url = english_editor.editor_url(self.page)

    def form(self, response):
        rows = response.context["rows"]
        data = {"piece_count": len(rows)}
        for index, row in enumerate(rows):
            data.update(
                {
                    f"piece-{index}-object": row["object"],
                    f"piece-{index}-path": row["segment"].path,
                    f"piece-{index}-norwegian": row["segment"].norwegian_text,
                    f"piece-{index}-original": row["english"],
                    f"piece-{index}-english": row["english"],
                }
            )
        return data

    def test_shows_pieces_and_saves_a_fix(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Velkommen til Ifi.")
        self.assertNotContains(response, 'value="None"')  # no English slug yet
        data = self.form(response)
        data["piece-0-english"] = "Buddy week"
        data["english_slug"] = "buddy-week"
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        row = SegmentTranslation.objects.get(segment_path="title")
        self.assertEqual(
            (row.english_text, row.source, row.translated_by),
            ("Buddy week", "human", self.admin),
        )
        self.assertEqual(EnglishSlug.objects.get(page=self.page).slug, "buddy-week")

    def test_fix_is_saved_against_the_norwegian_the_editor_saw(self):
        data = self.form(self.client.get(self.url))
        data["piece-0-english"] = "Buddy week"
        page = ArticlePage.objects.get(pk=self.page.pk)
        page.title = "Fadderuka"  # changed while the editor was typing
        page.save_revision().publish()
        self.client.post(self.url, data)
        self.assertEqual(
            SegmentTranslation.objects.get(source="human").norwegian_text, "Fadderuke"
        )

    def test_refuses_english_that_breaks_links(self):
        data = self.form(self.client.get(self.url))
        data["piece-0-english"] = 'Buddy <a id="a3">week</a>'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unrecognised id")
        self.assertFalse(SegmentTranslation.objects.filter(source="human").exists())

    def test_machine_translate_now(self):
        TranslationSettings.objects.update(auto_translate=False)
        self.client.post(self.url, {"machine_translate": "1"})
        self.assertFalse(
            stored_translations.missing_segments(
                ArticlePage.objects.get(pk=self.page.pk)
            )
        )

    def test_menu_group_lists_its_links(self):
        group = MenuGroup(locale=self.nb, title="Studentliv")
        group.links.add(
            MenuGroupLink(sort_order=0, label="Kart", url="https://example.com")
        )
        group.save()
        response = self.client.get(english_editor.editor_url(group))
        self.assertContains(response, "Studentliv")
        self.assertContains(response, "Kart")

    def test_people_without_edit_rights_are_refused(self):
        self.client.force_login(
            get_user_model().objects.create_user("visitor", password="pw")
        )
        self.assertNotEqual(self.client.get(self.url).status_code, 200)

    def test_english_button_on_pages_not_on_root(self):
        self.assertTrue(list(english_editor.page_button(self.page, self.admin)))
        root = Page.get_first_root_node()
        self.assertFalse(list(english_editor.page_button(root, self.admin)))


class StoredEnglishListTests(AutoTranslateTestCase):
    def test_superusers_may_look_but_not_change(self):
        self.article()
        auto_translate.translate_waiting()
        row = SegmentTranslation.objects.first()
        admin = get_user_model().objects.create_superuser(
            "admin", "a@example.com", "pw"
        )
        self.client.force_login(admin)
        index = reverse("stored_english:index")
        self.assertContains(self.client.get(index), "EN: Fadderuke")
        self.assertContains(self.client.get(index, {"q": "Fadderuke"}), "EN: Fadderuke")
        self.assertEqual(
            self.client.get(
                reverse("stored_english:inspect", args=[row.pk])
            ).status_code,
            200,
        )
        for name, args in (("add", []), ("edit", [row.pk]), ("delete", [row.pk])):
            response = self.client.get(reverse(f"stored_english:{name}", args=args))
            self.assertNotEqual(response.status_code, 200, name)

    def test_others_may_not_look(self):
        editor = get_user_model().objects.create_user(
            "editor", password="pw", is_staff=True
        )
        self.client.force_login(editor)
        self.assertNotEqual(
            self.client.get(reverse("stored_english:index")).status_code, 200
        )


class TreeTranslationTests(AutoTranslateTestCase):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_superuser(
            "admin", "a@example.com", "pw"
        )
        self.client.force_login(self.admin)
        self.parent = self.article("Forelder", "forelder")
        WaitingForEnglish.objects.all().delete()

    def test_subtree_marks_live_pages_and_runs_with_setting_off(self):
        child = ArticlePage(
            locale=self.nb,
            title="Barn",
            slug="barn",
            published_date=timezone.now().date(),
            body=[],
        )
        self.index.add_child(instance=child)
        child.save_revision().publish()
        WaitingForEnglish.objects.all().delete()
        TranslationSettings.objects.update(auto_translate=False)
        url = reverse("english_machine_translate_subtree", args=[self.index.pk])
        self.assertContains(self.client.get(url), "live page(s) under it")
        self.client.post(url)
        self.assertEqual(
            set(
                WaitingForEnglish.objects.values_list("requested_by_person", flat=True)
            ),
            {True},
        )
        self.assertEqual(self.waiting(), 3)  # index, parent article, child
        self.assertEqual(auto_translate.translate_waiting(), (3, 0))

    def test_automatic_rows_wait_while_setting_is_off(self):
        self.article("Ny", "ny")  # marked automatically on publish
        TranslationSettings.objects.update(auto_translate=False)
        self.assertEqual(auto_translate.translate_waiting(), (0, 0))
        self.assertEqual(self.waiting(), 1)

    def test_menu_is_translated_in_one_deepl_call(self):
        from ifi_home_app.models import Menu, MenuSlot

        group = MenuGroup(locale=self.nb, title="Studentliv")
        group.links.add(
            MenuGroupLink(sort_order=0, label="Kart", url="https://example.com")
        )
        group.links.add(
            MenuGroupLink(sort_order=1, label="Fadderuka", page=self.parent)
        )
        group.save()
        menu = Menu(key="sidemenu")
        menu.slots.add(MenuSlot(sort_order=0, group=group))
        menu.save()
        self.deepl.reset_mock()
        self.client.post(reverse("english_machine_translate_menu", args=[menu.pk]))
        self.deepl.assert_called_once_with(["Studentliv", "Kart", "Fadderuka"])
        with english():
            labels = [
                link.label for link in MenuGroup.objects.get(pk=group.pk).links.all()
            ]
        self.assertEqual(labels, ["EN: Kart", "EN: Fadderuka"])

    def test_editor_links_back_and_to_the_english_page(self):
        from wagtail.models import Site

        site = Site.objects.get(is_default_site=True)
        site.root_page = self.index
        site.save()  # clears Wagtail's cached site root paths
        response = self.client.get(english_editor.editor_url(self.parent))
        self.assertContains(
            response, reverse("wagtailadmin_pages:edit", args=[self.parent.pk])
        )
        self.assertContains(response, "View in English")
        index_editor = self.client.get(english_editor.editor_url(self.index))
        self.assertContains(
            index_editor, "Machine-translate this page and the pages under it"
        )
