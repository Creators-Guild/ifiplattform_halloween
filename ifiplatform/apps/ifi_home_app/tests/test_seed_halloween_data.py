# pylint: disable=C0114,C0115,C0116
from io import StringIO

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, tag
from wagtail.models import Page

from ifi_home_app.models import EnglishSlug
from ifi_home_app.translation import page_segments, stored_translations


@tag("slow")
class SeedHalloweenTests(TestCase):
    """The mock site's seed: no users, seeds only once, and fully English
    on /en/. An English failure names the Norwegian text to add to
    seed_halloween_data/constants.py (TRANSLATIONS or SAME_IN_ENGLISH)."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_halloween_data", stdout=StringIO())

    def seeded_objects(self):
        pages = Page.objects.filter(depth__gt=1).exclude(depth=2, slug="home")
        objects = [page.specific for page in pages]
        for model in apps.get_app_config("ifi_home_app").get_models():
            if not issubclass(model, Page) and page_segments.translated_field_names(
                model
            ):
                objects += list(model.objects.all())
        return objects

    def test_creates_no_users(self):
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_second_run_does_nothing(self):
        pages_before = Page.objects.count()
        out = StringIO()
        call_command("seed_halloween_data", stdout=out)
        self.assertIn("Already seeded", out.getvalue())
        self.assertEqual(Page.objects.count(), pages_before)

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
