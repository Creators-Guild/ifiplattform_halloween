"""The countdown to Halloween in the Halloween corner. Half built: the page
is there, the date and the ticking clock are the event issue's job (the
TODOs, here and in static/js/halloween_pages/countdown.js)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.shortcuts import render

OSLO = ZoneInfo("Europe/Oslo")


def next_halloween(today):
    """The next 31 October on or after today (a date)."""
    # TODO 1: this year's 31 October, or next year's if this year's is over.
    return None


def countdown_view(request):
    today = datetime.now(OSLO).date()
    target = next_halloween(today)
    return render(request, "halloween/countdown.html", {"target": target, "is_today": target == today})
