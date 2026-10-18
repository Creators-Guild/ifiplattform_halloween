"""The countdown to Halloween in the Halloween corner. The server works out
the date; static/js/halloween_pages/countdown.js makes the clock tick."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.shortcuts import render

OSLO = ZoneInfo("Europe/Oslo")


def next_halloween(today):
    """The next 31 October on or after today (a date)."""
    halloween = date(today.year, 10, 31)
    if halloween < today:
        halloween = date(today.year + 1, 10, 31)
    return halloween


def countdown_view(request):
    today = datetime.now(OSLO).date()
    target = next_halloween(today)
    return render(request, "halloween/countdown.html", {"target": target, "is_today": target == today})
