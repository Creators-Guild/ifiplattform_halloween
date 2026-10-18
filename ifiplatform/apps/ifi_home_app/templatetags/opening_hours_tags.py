"""{% get_opening_hours as places %}: the home page's "Open now" box."""

from django import template

from ..opening_hours import hours_on, is_open, now_in_oslo
from ..opening_hours_data import PLACES

register = template.Library()


@register.simple_tag
def get_opening_hours():
    """Every place with today's hours (None when closed all day) and whether
    it's open right now."""
    now = now_in_oslo()
    return [
        {"name": place["name"], "today": hours_on(place, now.weekday()), "open": is_open(place, now)}
        for place in PLACES
    ]
