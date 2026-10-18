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
    """True if place is open at now (a datetime), False if not. A closing
    time at or before the opening time means it closes after midnight, so
    just after midnight yesterday's hours can still be running."""
    time = now.strftime("%H:%M")
    today = hours_on(place, now.weekday())
    if today:
        opens, closes = today
        if opens < closes and opens <= time < closes:
            return True
        if closes <= opens and time >= opens:
            return True
    yesterday = hours_on(place, (now.weekday() - 1) % 7)
    if yesterday:
        opens, closes = yesterday
        if closes <= opens and time < closes:
            return True
    return False
