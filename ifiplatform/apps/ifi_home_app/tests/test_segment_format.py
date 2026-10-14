# pylint: disable=C0114,C0115,C0116
"""Golden format tests: fixed example objects -> the exact pieces (place,
Norwegian text in stored form, hash) that stored English is keyed by.

If one fails, the way fields are split into pieces changed (a
wagtail-localize upgrade, or a change to page_segments.py). Every stored
English row would stop matching, and DeepL would redo everything, losing
people's fixes. Don't update golden_segments.json to make it pass: make
the extraction produce these pieces again. The only legitimate update is a
new case for a new kind of content. Any replacement for wagtail-localize
must pass these unchanged (docs/claude_context/translation_overlay.md).
"""

import json
from pathlib import Path

from django.test import TestCase

from ifi_home_app.models import ArticlePage, MenuGroupLink
from ifi_home_app.models.article.unions import UnionPage
from ifi_home_app.translation import page_segments

GOLDEN = Path(__file__).with_name("golden_segments.json")

# Fixed block ids, so paths never change between runs.
IDS = {
    name: f"00000000-0000-4000-8000-{number:012d}"
    for number, name in enumerate(
        [
            "heading",
            "paragraph",
            "image",
            "columns",
            "column",
            "column_paragraph",
            "member",
            "vacant",
            "duty_1",
            "duty_2",
        ],
        start=1,
    )
}


def _stream(model, name, raw):
    return model._meta.get_field(name).to_python(raw)


def golden_objects():
    """name -> unsaved object with every kind of translated content."""
    article = ArticlePage(
        title="Fadderuke & velkomst",
        seo_title="",
        search_description="Alt om fadderuka.",
        intro=(
            "<p>Velkommen til Ifi. Her er alt du trenger.</p>"
            '<p>Les mer om <a linktype="page" id="5">fadderuka</a> og '
            '<a href="https://www.uio.no">UiO</a> her.</p>'
        ),
        hero_image_title="Plenen",
        hero_image_alt="Studenter på plenen",
        hero_image_caption="Første dag, 2026",
        body=None,
    )
    article.body = _stream(
        ArticlePage,
        "body",
        [
            {
                "type": "heading",
                "id": IDS["heading"],
                "value": {"text": "Program", "level": "h2"},
            },
            {
                "type": "paragraph",
                "id": IDS["paragraph"],
                "value": {
                    "text": "<p>Første dag er <b>mandag</b>. Ta med:</p>"
                    "<ul><li>Studentkort</li><li>Godt humør</li></ul>"
                },
            },
            {
                "type": "image",
                "id": IDS["image"],
                "value": {
                    "image": None,
                    "alt_text": "Kart",
                    "caption": "Kart over Ifi",
                },
            },
            {
                "type": "multi_column",
                "id": IDS["columns"],
                "value": {
                    "columns": [
                        {
                            "type": "item",
                            "id": IDS["column"],
                            "value": {
                                "title": "Kolonne",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "id": IDS["column_paragraph"],
                                        "value": {"text": "<p>Inni kolonnen.</p>"},
                                    }
                                ],
                            },
                        }
                    ],
                    "column_alignment": "top",
                },
            },
        ],
    )

    union = UnionPage(title="Navet", sitting_members=None)
    union.sitting_members = _stream(
        UnionPage,
        "sitting_members",
        [
            {
                "type": "member",
                "id": IDS["member"],
                "value": {
                    "name": "Kari Nordmann",  # a person's name: never a piece
                    "role": "Leder",
                    "role_nickname": "Husets sjel",
                    "school_email": "kari@ifi.uio.no",
                    "picture": None,
                    "responsibilities": [
                        {
                            "type": "item",
                            "id": IDS["duty_1"],
                            "value": "<p>Driver <i>Navet</i>.</p>",
                        },
                        {
                            "type": "item",
                            "id": IDS["duty_2"],
                            "value": "<p>Frivillige.</p>",
                        },
                    ],
                    "availability": "opening_soon",
                    "availability_note": "Etter generalforsamlingen",
                },
            },
            {
                "type": "member",
                "id": IDS["vacant"],
                "value": {
                    "name": "",
                    "role": "Kasserer",
                    "role_nickname": "",
                    "school_email": "",
                    "picture": None,
                    "responsibilities": [],
                    "availability": "open",
                    "availability_note": "",
                },
            },
        ],
    )

    link = MenuGroupLink(
        label="Ifi", description="Peoply", label_prefix="Stillinger hos"
    )
    return {"article": article, "union": union, "menu_link": link}


def pieces(obj):
    return [
        [segment.path, segment.norwegian_text, str(segment.norwegian_hash)]
        for segment in page_segments.extract_segments(obj)
    ]


class GoldenFormatTests(TestCase):
    def test_pieces_are_unchanged(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        objects = golden_objects()
        self.assertEqual(sorted(objects), sorted(golden))
        for name, obj in objects.items():
            with self.subTest(name):
                self.assertEqual(pieces(obj), golden[name])

    def test_english_goes_back_in_place(self):
        article = golden_objects()["article"]
        english = {
            segment: f"[EN] {segment.norwegian_text}"
            for segment in page_segments.extract_segments(article, "intro")
        }
        self.assertHTMLEqual(
            page_segments.apply_translations(article, "intro", english),
            "<p>[EN] Velkommen til Ifi. Her er alt du trenger.</p>"
            '<p>[EN] Les mer om <a linktype="page" id="5">fadderuka</a> og '
            '<a href="https://www.uio.no">UiO</a> her.</p>',
        )
