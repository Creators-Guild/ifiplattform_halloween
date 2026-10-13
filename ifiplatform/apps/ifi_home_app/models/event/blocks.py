"""StreamField blocks used by EventPage.

Design rationale/history: docs/claude_context/event_models.md"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .constants import EVENT_CALENDAR_COLOR_CHOICES, UNION_ROLE_CHOICES


def event_union_block():
    """A student union involved in an event, plus their role."""
    return blocks.StructBlock(
        [
            (
                "union",
                blocks.PageChooserBlock(
                    page_type="ifi_home_app.UnionPage",
                    required=True,
                    help_text="The student union involved.",
                ),
            ),
            (
                "role",
                blocks.ChoiceBlock(
                    choices=UNION_ROLE_CHOICES,
                    default="host",
                ),
            ),
        ],
        icon="group",
        label="Union",
    )


def calendar_legend_entry_block():
    """One row of a parent event's own color legend (calendar_legend below)."""
    return blocks.StructBlock(
        [
            (
                "color",
                blocks.ChoiceBlock(
                    choices=[
                        (key, label)
                        for key, label in EVENT_CALENDAR_COLOR_CHOICES
                        if key not in ("", "custom")
                    ],
                    default="blue",
                ),
            ),
            (
                "label",
                blocks.CharBlock(
                    max_length=60,
                    help_text='What this color means, e.g. "Study-relevant".',
                ),
            ),
        ],
        icon="tag",
        label="Legend entry",
    )


def location_map_link_block():
    """One titled link to a map for one of the event's locations."""
    return blocks.StructBlock(
        [
            (
                "title",
                blocks.CharBlock(
                    max_length=100,
                    required=False,
                    help_text='Optional -- link text, e.g. "Google Maps". Defaults to "View on map" if left blank.',
                ),
            ),
            (
                "url",
                blocks.URLBlock(
                    required=True,
                    help_text="Link to a map for this location.",
                ),
            ),
        ],
        icon="site",
        label="Map Link",
    )
