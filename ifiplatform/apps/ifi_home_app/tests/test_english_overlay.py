# pylint: disable=C0114,C0115,C0116
"""English overlay (translate on read, database guard, storage, cleanup,
English slugs, English preview) -- see
docs/claude_context/translation_overlay.md."""

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.utils import timezone, translation
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Locale, Page, Site

from ifi_home_app.models import (
    ArticleIndexPage,
    ArticlePage,
    EnglishSlug,
    MenuGroup,
    MenuGroupLink,
    SegmentTranslation,
)
from ifi_home_app.translation import english_urls, page_segments, stored_translations
from ifi_home_app.translation.english_overlay import (
    MEMO_ATTR,
    EnglishWriteBlocked,
    english,
    english_active,
    raw_norwegian,
    translation_status,
)
from ifi_home_app.translation.page_segments import Segment

INTRO = (
    "<p>Velkommen til Ifi. Her er alt du trenger.</p>"
    '<p>Les mer om <a linktype="page" id="{id}">Fadderuka</a> her.</p>'
)
ENGLISH = {
    "Fadderuke": "Freshers' week",
    "Velkommen til Ifi. Her er alt du trenger.": "Welcome to Ifi. Here is all you need.",
    'Les mer om <a id="a1">Fadderuka</a> her.': 'Read more about <a id="a1">Freshers</a> here.',
    "Studenter på plenen": "Students on the lawn",
    "Program": "Schedule",
    "Første dag er <b>mandag</b>.": "The first day is <b>Monday</b>.",
    "Kolonne": "Column",
    "Inni kolonnen.": "Inside the column.",
}


def store_deepl(page, english_by_norwegian):
    stored_translations.save_machine(
        page,
        {
            segment: english_by_norwegian[segment.norwegian_text]
            for segment in page_segments.extract_segments(page)
            if segment.norwegian_text in english_by_norwegian
        },
    )


class OverlayTestCase(TestCase):
    def setUp(self):
        self.nb, _ = Locale.objects.get_or_create(language_code="nb")
        self.index = ArticleIndexPage(
            locale=self.nb, title="Artikler", slug="artikler", section="info_articles"
        )
        Page.get_first_root_node().add_child(instance=self.index)
        self.index.save_revision().publish()
        self.article = self.make_article("Fadderuke", "fadderuke")
        store_deepl(self.article, ENGLISH)

    def make_article(self, title, slug, parent=None):
        article = ArticlePage(
            locale=self.nb,
            title=title,
            slug=slug,
            published_date=timezone.now().date(),
            intro=INTRO.format(id=self.index.id),
            hero_image_caption="Studenter på plenen",
            body=[
                ("heading", {"text": "Program", "level": "h2"}),
                ("paragraph", {"text": "<p>Første dag er <b>mandag</b>.</p>"}),
                (
                    "multi_column",
                    {
                        "columns": [
                            {
                                "title": "Kolonne",
                                "content": [
                                    ("paragraph", {"text": "<p>Inni kolonnen.</p>"})
                                ],
                            }
                        ],
                        "column_alignment": "top",
                    },
                ),
            ],
        )
        (parent or self.index).add_child(instance=article)
        article.save_revision().publish()
        return article

    def fresh(self):
        return ArticlePage.objects.get(pk=self.article.pk)


class TranslatedFieldTests(OverlayTestCase):
    def test_norwegian_unless_english_is_on(self):
        self.assertEqual(self.fresh().title, "Fadderuke")
        with english():
            self.assertEqual(self.fresh().title, "Freshers' week")
            with raw_norwegian():
                self.assertEqual(self.fresh().title, "Fadderuke")

    def test_plain_and_rich_text_keep_links(self):
        with english():
            page = self.fresh()
            caption, intro = page.hero_image_caption, page.intro
        self.assertEqual(caption, "Students on the lawn")
        self.assertIn("Welcome to Ifi. Here is all you need.", intro)
        self.assertIn("Read more about", intro)
        self.assertIn('linktype="page"', intro)
        self.assertIn(f'id="{self.index.id}"', intro)

    def test_streamfield_nested_blocks_and_norwegian_untouched(self):
        with english():
            page = self.fresh()
            body = page.body
            column = body[2].value["columns"][0]
            self.assertEqual(body[0].value["text"], "Schedule")
            self.assertIn(
                "The first day is <b>Monday</b>.", body[1].value["text"].source
            )
            self.assertEqual(column["title"], "Column")
            self.assertIn(
                "Inside the column.", column["content"][0].value["text"].source
            )
            with raw_norwegian():
                self.assertEqual(page.body[0].value["text"], "Program")

    def test_reading_title_does_not_translate_body(self):
        with english():
            page = self.fresh()
            page.title  # pylint: disable=pointless-statement
        self.assertEqual(set(page.__dict__[MEMO_ATTR]), {"title"})

    def test_plain_pages_children_and_specific(self):
        with english():
            child = self.index.get_children().first()
            self.assertIs(type(child), Page)
            self.assertEqual(child.title, "Freshers' week")
            self.assertEqual(child.specific.title, "Freshers' week")
            self.assertEqual(child.specific.hero_image_caption, "Students on the lawn")

    def test_changed_norwegian_shows_norwegian_until_translated(self):
        page = self.fresh()
        page.hero_image_caption = "Studenter i sola"
        page.save_revision().publish()
        with english():
            page = self.fresh()
            self.assertEqual(page.hero_image_caption, "Studenter i sola")
            self.assertEqual(page.title, "Freshers' week")

    def test_human_fix_survives_unrelated_edit(self):
        stored_translations.save_human(
            self.article, Segment("title", "Fadderuke"), "Buddy week", None
        )
        page = self.fresh()
        page.hero_image_caption = "Studenter i sola"
        page.save_revision().publish()
        with english():
            self.assertEqual(self.fresh().title, "Buddy week")

    def test_bad_english_falls_back_to_norwegian(self):
        SegmentTranslation.objects.filter(norwegian_text__startswith="Les mer").update(
            english_text='Read <a id="a9">more</a>'
        )
        with english(), self.assertLogs("ifi_home_app.translation.english_overlay"):
            intro = self.fresh().intro
        self.assertIn("Velkommen til Ifi.", intro)

    def test_menu_group_and_links(self):
        group = MenuGroup(locale=self.nb, title="Studentliv", short_title="Liv")
        group.links.add(
            MenuGroupLink(sort_order=0, label="Fadderuka", page=self.article)
        )
        group.links.add(
            MenuGroupLink(sort_order=1, label="Kart", url="https://example.com")
        )
        group.save()
        store_deepl(group, {"Studentliv": "Student life"})
        store_deepl(group.links.get(sort_order=0), {"Fadderuka": "Freshers"})
        with english():
            group = MenuGroup.objects.get(pk=group.pk)
            self.assertEqual(group.title, "Student life")
            self.assertEqual(group.short_title, "Liv")
            self.assertEqual(
                [link.label for link in group.links.all()], ["Freshers", "Kart"]
            )


class DatabaseGuardTests(OverlayTestCase):
    def test_writes_refused_while_english_is_shown(self):
        page = self.fresh()
        blocked = []
        attempts = {
            "save": page.save,
            "save_revision": page.save_revision,
            "update": lambda: ArticlePage.objects.filter(pk=page.pk).update(intro="x"),
            "bulk_update": lambda: ArticlePage.objects.bulk_update([page], ["intro"]),
            "snippet save": lambda: MenuGroup(locale=self.nb, title="X").save(),
        }
        with english():
            for name, attempt in attempts.items():
                try:
                    with transaction.atomic():
                        attempt()
                except EnglishWriteBlocked:
                    blocked.append(name)
            Locale.objects.get_or_create(language_code="de")  # other tables still work
        self.assertEqual(blocked, list(attempts))
        with raw_norwegian():  # the refused attempts left Norwegian in memory
            self.assertEqual(page.title, "Fadderuke")
        page.save()  # English off: works again
        self.assertEqual(Page.objects.get(pk=page.pk).title, "Fadderuke")

    def test_raw_mode_save_stores_norwegian(self):
        with english():
            page = self.fresh()
            page.title  # pylint: disable=pointless-statement
            with raw_norwegian():
                page.save()
        self.assertEqual(Page.objects.get(pk=page.pk).title, "Fadderuke")

    def test_refresh_and_deferred_loading_keep_norwegian(self):
        with english():
            page = ArticlePage.objects.defer("hero_image_caption").get(
                pk=self.article.pk
            )
            self.assertEqual(page.hero_image_caption, "Students on the lawn")
            page.refresh_from_db()
            self.assertEqual(page.title, "Freshers' week")
            with raw_norwegian():
                self.assertEqual(page.hero_image_caption, "Studenter på plenen")
                self.assertEqual(page.title, "Fadderuke")

    def test_english_off_again_after_an_error(self):
        with self.assertRaises(ZeroDivisionError):
            with english():
                1 / 0  # pylint: disable=pointless-statement
        self.assertFalse(english_active())

    def test_write_blocker_on_this_connection(self):
        from ifi_home_app.translation.english_overlay import block_english_writes

        self.assertIn(block_english_writes, connection.execute_wrappers)


class StorageTests(OverlayTestCase):
    def test_lookup_is_one_query_and_remembered(self):
        page = self.fresh()
        with self.assertNumQueries(1):
            stored_translations.lookup(page)
            stored_translations.lookup(page)

    def test_hash_matches_wagtail_localize(self):
        from wagtail_localize.models import String

        text = "Første dag er <b>mandag</b>."
        self.assertEqual(page_segments.segment_hash(text), String._get_data_hash(text))

    def test_deepl_never_overwrites_a_person(self):
        segment = Segment("title", "Fadderuke")
        stored_translations.save_human(self.article, segment, "Buddy week", None)
        stored_translations.save_machine(self.article, {segment: "Freshers week"})
        row = SegmentTranslation.objects.get(segment_path="title")
        self.assertEqual((row.english_text, row.source), ("Buddy week", "human"))

    def test_person_replaces_deepl(self):
        user = get_user_model().objects.create(username="kari")
        segment = Segment("title", "Fadderuke")
        stored_translations.save_human(self.article, segment, "Buddy week", user)
        row = SegmentTranslation.objects.get(segment_path="title")
        self.assertEqual(
            (row.english_text, row.source, row.translated_by),
            ("Buddy week", "human", user),
        )

    def test_missing_segments(self):
        SegmentTranslation.objects.filter(segment_path="title").delete()
        missing = stored_translations.missing_segments(self.fresh())
        self.assertIn(Segment("title", "Fadderuke"), missing)
        self.assertNotIn(Segment("hero_image_caption", "Studenter på plenen"), missing)

    def test_empty_text_is_not_a_piece(self):
        page = self.fresh()
        page.hero_image_caption = ""
        page.body = [("multi_column", {"columns": [{"title": "", "content": []}]})]
        page.save_revision().publish()
        paths = [
            segment.path for segment in page_segments.extract_segments(self.fresh())
        ]
        self.assertNotIn("hero_image_caption", paths)
        self.assertFalse([path for path in paths if path.startswith("body")])

    def test_check_english(self):
        segment = Segment("intro", 'Les <a id="a1">her</a>')
        page_segments.check_english(segment, 'Read <a id="a1">here</a>')
        with self.assertRaises(ValueError):
            page_segments.check_english(segment, 'Read <a id="a2">here</a>')

    def test_excluded_block_paths_and_technical_fields(self):
        from django.core.exceptions import ImproperlyConfigured
        from ifi_home_app.models.article.unions import UnionPage

        self.assertIn(
            "sitting_members → member → role", page_segments.places(UnionPage)
        )
        self.assertNotIn(
            "sitting_members → member → name", page_segments.places(UnionPage)
        )
        for name in ("email", "status", "logo"):  # email, choice, image
            with self.assertRaises(ImproperlyConfigured):
                page_segments.check_translated_field(UnionPage, name)

    def test_status_counts(self):
        stored_translations.save_human(
            self.article, Segment("title", "Fadderuke"), "Buddy week", None
        )
        status = translation_status(self.fresh())
        self.assertEqual(status.human, 1)
        self.assertEqual(status.missing, 0)
        self.assertEqual(status.total, status.human + status.deepl)


class CleanupTests(OverlayTestCase):
    def rows(self):
        return set(
            SegmentTranslation.objects.values_list("segment_path", "norwegian_text")
        )

    def test_deleted_page_loses_its_rows(self):
        self.article.delete()
        stored_translations.cleanup()
        self.assertEqual(SegmentTranslation.objects.count(), 0)

    def test_removed_block_loses_its_rows(self):
        page = self.fresh()
        heading_id = page.body[0].id
        page.body = page.body.get_prep_value()[1:]
        page.save_revision().publish()
        stored_translations.cleanup()
        self.assertFalse(
            SegmentTranslation.objects.filter(
                segment_path=f"body.{heading_id}.text"
            ).exists()
        )

    def test_old_deepl_goes_newest_old_human_stays(self):
        stored_translations.save_human(
            self.article, Segment("title", "Fadderuke"), "Buddy week", None
        )
        caption = Segment("hero_image_caption", "Studenter på plenen")
        page = self.fresh()
        page.title, page.hero_image_caption = "Fadderuka 2027", "Studenter i sola"
        page.save_revision().publish()
        stored_translations.cleanup()
        rows = self.rows()
        self.assertIn(("title", "Fadderuke"), rows)  # kept as a later suggestion
        self.assertNotIn((caption.path, caption.norwegian_text), rows)

    def test_draft_deletes_nothing(self):
        page = self.fresh()
        page.hero_image_caption = "Studenter i sola"
        page.save_revision()  # draft only
        before = self.rows()
        stored_translations.cleanup()
        self.assertEqual(self.rows(), before)

    def test_deleted_user_keeps_the_fix(self):
        user = get_user_model().objects.create(username="kari")
        stored_translations.save_human(
            self.article, Segment("title", "Fadderuke"), "Buddy week", user
        )
        user.delete()
        row = SegmentTranslation.objects.get(segment_path="title")
        self.assertEqual((row.source, row.translated_by), ("human", None))


class EnglishSlugTests(OverlayTestCase):
    def test_unique_among_siblings_also_against_norwegian_slugs(self):
        sibling = self.make_article("Arrangementer", "freshers-week")
        slug = english_urls.set_english_slug(self.article, "Freshers' week", "deepl")
        self.assertEqual(slug, "freshers-week-2")
        self.assertEqual(
            english_urls.set_english_slug(sibling, "Events", "deepl"), "events"
        )

    def test_path_falls_back_to_norwegian_slug(self):
        root = Page.get_first_root_node()
        self.assertEqual(
            english_urls.english_url_path(self.article, root.depth),
            "artikler/fadderuke/",
        )
        english_urls.set_english_slug(self.index, "Articles", "deepl")
        english_urls.set_english_slug(self.article, "Freshers' week", "deepl")
        self.assertEqual(
            english_urls.english_url_path(self.article, root.depth),
            "articles/freshers-week/",
        )

    def test_find_child(self):
        english_urls.set_english_slug(self.article, "Freshers' week", "deepl")
        child, by_english = english_urls.find_child(self.index, "freshers-week")
        self.assertEqual((child.pk, by_english), (self.article.pk, True))
        child, by_english = english_urls.find_child(self.index, "fadderuke")
        self.assertEqual((child.pk, by_english), (self.article.pk, False))
        self.assertEqual(english_urls.find_child(self.index, "nope"), (None, False))

    def test_set_once_from_first_title(self):
        english_urls.set_english_slug_if_missing(self.article, "Freshers' week")
        english_urls.set_english_slug_if_missing(self.article, "Welcome week")
        self.assertEqual(
            EnglishSlug.objects.get(page=self.article).slug, "freshers-week"
        )

    def test_one_query_per_request_scope(self):
        root = Page.get_first_root_node()
        with english_urls.request_scope():
            english_urls.english_url_path(self.article, root.depth)
            with self.assertNumQueries(0):
                english_urls.english_url_path(self.article, root.depth)
                english_urls.english_url_path(self.index, root.depth)


class AddressChangeRedirectTests(OverlayTestCase):
    def setUp(self):
        super().setUp()
        site = Site.objects.get(is_default_site=True)
        site.root_page = Page.get_first_root_node()
        site.save()
        english_urls.set_english_slug(self.index, "Articles", "human")
        self.other = ArticleIndexPage(
            locale=self.nb, title="Annet", slug="annet", section="news"
        )
        Page.get_first_root_node().add_child(instance=self.other)
        self.other.save_revision().publish()

    def redirects(self):
        return {
            redirect.old_path: redirect.link
            for redirect in Redirect.objects.select_related("redirect_page")
        }

    def redirects_after(self, change, admin_language):
        """Redirects made by change() with the admin in admin_language;
        rolled back afterwards."""
        with transaction.atomic():
            with translation.override(admin_language):
                with self.captureOnCommitCallbacks(execute=True):
                    change()
            redirects = self.redirects()
            transaction.set_rollback(True)
        return redirects

    def test_moved_page_redirects_in_both_languages(self):
        english_urls.set_english_slug(self.article, "Freshers' week", "human")

        def move():
            ArticlePage.objects.get(pk=self.article.pk).move(
                ArticleIndexPage.objects.get(pk=self.other.pk), pos="last-child"
            )

        for language in ("nb", "en"):
            redirects = self.redirects_after(move, language)
            self.assertEqual(
                redirects.get("/en/articles/freshers-week"),
                "/en/annet/freshers-week/",
                language,
            )
            self.assertIn("/nb/artikler/fadderuke", redirects, language)
            # Wagtail's handler under "en" used to delete every redirect.
            self.assertIn("/en/artikler", redirects, language)

    def test_norwegian_slug_change_moves_english_fallback_address(self):
        def rename():
            page = ArticlePage.objects.get(pk=self.article.pk)
            page.slug = "fadderuka"
            page.save_revision().publish()

        for language in ("nb", "en"):
            redirects = self.redirects_after(rename, language)
            self.assertEqual(
                redirects.get("/en/articles/fadderuke"),
                "/en/articles/fadderuka/",
                language,
            )
            self.assertIn("/nb/artikler/fadderuke", redirects, language)

    def test_english_slug_keeps_english_address_on_norwegian_slug_change(self):
        english_urls.set_english_slug(self.article, "Freshers' week", "human")
        page = ArticlePage.objects.get(pk=self.article.pk)
        page.slug = "fadderuka"
        with self.captureOnCommitCallbacks(execute=True):
            page.save_revision().publish()
        redirects = self.redirects()
        self.assertIn("/nb/artikler/fadderuke", redirects)
        self.assertNotIn("/en/articles/freshers-week", redirects)


@override_settings(ALLOWED_HOSTS=["*"])
class EnglishPreviewTests(OverlayTestCase):
    def test_english_preview(self):
        response = self.fresh().make_preview_request(preview_mode="en")
        self.assertContains(response, "Freshers&#x27; week")
        self.assertContains(response, "The first day is <b>Monday</b>.", html=False)

    def test_norwegian_preview(self):
        response = self.fresh().make_preview_request(preview_mode="")
        self.assertContains(response, "Fadderuke")
        self.assertNotContains(response, "Freshers")
