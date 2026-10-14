# pylint: disable=C0114,C0115,C0116
"""Safety net for the English overlay: with fake English stored for every
piece, no /en/ page may show a Norwegian title, menu label or other plain
text piece. Code that reads around the model fields (.values("title"),
raw SQL, a cached dict built under /nb/) shows Norwegian on /en/; this
finds it. See docs/claude_context/translation_overlay.md."""

import re
from html.parser import HTMLParser
from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, tag
from django.utils import translation
from wagtail.models import Page

from ifi_home_app.models import SegmentTranslation
from ifi_home_app.translation import page_segments, stored_translations

MARK = "EN·"
MAX_PAGES = 300
SKIPPED_PREFIXES = ("/static/", "/media/", "/admin/", "/wagtail-admin/")


class _VisibleText(HTMLParser):
    """Text nodes outside <script>/<style>, whitespace collapsed."""

    def __init__(self):
        super().__init__()
        self.texts, self._hidden = [], 0

    def handle_starttag(self, tag, attrs):
        self._hidden += tag in ("script", "style")

    def handle_endtag(self, tag):
        self._hidden -= tag in ("script", "style") and self._hidden > 0

    def handle_data(self, data):
        text = " ".join(data.split())
        if text and not self._hidden:
            self.texts.append(text)


def _translated_objects():
    objects = [page.specific for page in Page.objects.filter(depth__gt=1)]
    for model in apps.get_app_config("ifi_home_app").get_models():
        if not issubclass(model, Page) and page_segments.translated_field_names(model):
            objects += list(model.objects.all())
    return objects


@tag("slow")
class FakeEnglishCrawlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_dev_data", "--force", stdout=StringIO())
        SegmentTranslation.objects.all().delete()
        cls.norwegian = set()
        for obj in _translated_objects():
            segments = page_segments.extract_segments(obj)
            stored_translations.save_machine(
                obj, {segment: MARK + segment.norwegian_text for segment in segments}
            )
            cls.norwegian.update(
                page_segments.plain_text(segment.norwegian_text).strip()
                for segment in segments
                if "<" not in segment.norwegian_text
            )

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)  # /en/ requests leave "en" on

    def test_no_norwegian_on_english_pages(self):
        to_visit, visited, leaks = ["/en/"], set(), []
        while to_visit and len(visited) < MAX_PAGES:
            url = to_visit.pop()
            if url in visited:
                continue
            visited.add(url)
            response = self.client.get(url, follow=True)
            if (
                response.status_code != 200
                or "text/html" not in response["Content-Type"]
            ):
                continue
            html = response.content.decode()
            parser = _VisibleText()
            parser.feed(html)
            leaks += [
                f"{url}: {text!r}" for text in parser.texts if text in self.norwegian
            ]
            for href in re.findall(r'href="(/en/[^"#?]*)', html):
                if not href.startswith(tuple("/en" + p for p in SKIPPED_PREFIXES)):
                    to_visit.append(href)
        self.assertGreater(len(visited), 20, "the crawl found too few pages")
        self.assertEqual(sorted(set(leaks)), [], "Norwegian text on /en/ pages")
