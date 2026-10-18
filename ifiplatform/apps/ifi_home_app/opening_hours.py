"""Opening hours for the home page's "Open now" box: today's hours and
whether a place is open right now. The data is in opening_hours_data.py.
Times are Norwegian time, whatever the server's own time zone is."""

from datetime import datetime
from zoneinfo import ZoneInfo

OSLO = ZoneInfo("Europe/Oslo")


def now_in_oslo():
    return datetime.now(OSLO)


def hours_on(place, day):
    """The (open, close) pair for weekday day (0 is Monday), or None."""
    return place["hours"][day]


def is_open(place, now):
    """True if place is open at now (a datetime), False if not."""
    hours = hours_on(place, now.weekday())
    if hours is None:
        return False
    opens, closes = hours
    return opens <= now.strftime("%H:%M") < closes
