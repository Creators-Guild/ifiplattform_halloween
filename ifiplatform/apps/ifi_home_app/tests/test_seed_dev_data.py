# pylint: disable=C0114,C0115,C0116
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase, tag
from wagtail.models import Page

from ifi_home_app.models import EnglishSlug
from ifi_home_app.translation import page_segments, stored_translations


@tag("slow")
class SeedEnglishTests(TestCase):
    """The seeded site is fully English on /en/: no "not translated yet"
    notices, English addresses everywhere. A failure names the Norwegian
    text to add to seed_dev_data/constants.py (TRANSLATIONS or
    SAME_IN_ENGLISH)."""

    @classmethod
    def setUpTestData(cls):
        # --force: the test runner always has DEBUG off.
        call_command("seed_dev_data", "--force", stdout=StringIO())

    def seeded_objects(self):
        # Not Wagtail's own "Welcome" placeholder page from its migrations.
        pages = Page.objects.filter(depth__gt=1).exclude(depth=2, slug="home")
        objects = [page.specific for page in pages]
        for model in apps.get_app_config("ifi_home_app").get_models():
            if not issubclass(model, Page) and page_segments.translated_field_names(
                model
            ):
                objects += list(model.objects.all())
        return objects

    def test_every_piece_has_english(self):
        missing = []
        for obj in self.seeded_objects():
            rows = stored_translations.lookup(obj)
            missing += [
                f"{type(obj).__name__} {obj}: {segment.path} = {segment.norwegian_text!r}"
                for segment in page_segments.extract_segments(obj)
                if (segment.path, segment.norwegian_hash) not in rows
            ]
        self.assertEqual(missing, [], "Seeded text without English")

    def test_every_page_has_an_english_slug(self):
        without_slug = (
            Page.objects.filter(depth__gt=1)
            .exclude(depth=2, slug="home")
            .exclude(pk__in=EnglishSlug.objects.values("page_id"))
        )
        self.assertEqual(list(without_slug.values_list("title", flat=True)), [])
