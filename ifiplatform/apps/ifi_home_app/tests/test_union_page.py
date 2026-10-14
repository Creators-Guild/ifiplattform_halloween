# pylint: disable=C0114,C0115,C0116
from django.template.loader import render_to_string
from django.test import TestCase

from wagtail.models import Locale, Page

from ifi_home_app.models.article.unions import UnionPage

CARD_TEMPLATE = "info_articles/partials/union_position_card.html"


def _make_union(sitting_members, **kwargs):
    root = Page.get_first_root_node()
    nb_locale, _ = Locale.objects.get_or_create(language_code="nb")
    kwargs.setdefault("title", "Test Union")
    kwargs.setdefault("slug", "test-union")
    kwargs.setdefault("locale", nb_locale)
    union = UnionPage(sitting_members=sitting_members, **kwargs)
    root.add_child(instance=union)
    union.save_revision().publish()
    return union


class FilledAndOpenPositionsTests(TestCase):
    """UnionPage.filled_positions/open_positions -- independent filters
    over the same sitting_members list, not a partition. See
    docs/claude_context/article_unions.md."""

    def test_plain_filled_position_is_only_in_filled_positions(self):
        union = _make_union(
            [
                ("member", {"name": "Ada", "role": "Leder"}),
            ]
        )

        self.assertEqual(len(union.filled_positions), 1)
        self.assertEqual(union.open_positions, [])

    def test_vacant_open_position_is_only_in_open_positions(self):
        union = _make_union(
            [
                ("member", {"role": "Nestleder", "availability": "open"}),
            ]
        )

        self.assertEqual(union.filled_positions, [])
        self.assertEqual(len(union.open_positions), 1)

    def test_filled_position_opening_soon_appears_in_both(self):
        union = _make_union(
            [
                (
                    "member",
                    {"name": "Ada", "role": "Leder", "availability": "opening_soon"},
                ),
            ]
        )

        self.assertEqual(len(union.filled_positions), 1)
        self.assertEqual(len(union.open_positions), 1)
        self.assertEqual(union.filled_positions[0].value["name"], "Ada")
        self.assertEqual(union.open_positions[0].value["name"], "Ada")

    def test_blank_name_string_counts_as_vacant(self):
        union = _make_union(
            [
                ("member", {"name": "", "role": "Nestleder"}),
            ]
        )

        self.assertEqual(union.filled_positions, [])


class UnionPositionCardRenderTests(TestCase):
    """Renders union_position_card.html directly (not the whole page --
    home_base.html's sidemenu/breadcrumbs need a full site tree that's
    irrelevant to this partial) -- catches template syntax errors in the
    two show_description_inline modes."""

    def test_sitting_member_card_hides_responsibilities_behind_info_icon(self):
        union = _make_union(
            [
                (
                    "member",
                    {
                        "name": "Ada",
                        "role": "Leder",
                        "role_nickname": "Guild Master",
                        "responsibilities": ["Leads the union."],
                        "availability": "opening_soon",
                        "availability_note": "After the next generalforsamling",
                    },
                ),
            ]
        )
        union = UnionPage.objects.get(
            pk=union.pk
        )  # reload -- round-trips through StreamField JSON
        block = union.filled_positions[0]

        html = render_to_string(
            CARD_TEMPLATE, {"block": block, "show_description_inline": False}
        )

        self.assertIn("Ada", html)
        self.assertIn("Guild Master", html)
        self.assertIn("After the next generalforsamling", html)
        self.assertIn(
            "position-info-widget", html
        )  # icon popup for the responsibilities
        self.assertIn(
            "Leads the union", html
        )  # server-rendered into the (JS-hidden) popup panel

    def test_open_position_card_shows_responsibilities_inline_and_vacant_label(self):
        union = _make_union(
            [
                (
                    "member",
                    {
                        "role": "Nestleder",
                        "responsibilities": ["Deputy duties."],
                        "availability": "open",
                    },
                ),
            ]
        )
        union = UnionPage.objects.get(pk=union.pk)
        block = union.open_positions[0]

        html = render_to_string(
            CARD_TEMPLATE, {"block": block, "show_description_inline": True}
        )

        self.assertIn("Vacant", html)
        self.assertIn("Deputy duties", html)  # shown inline, not behind an icon
        self.assertNotIn("position-info-widget", html)
