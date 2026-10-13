"""Date-range and month-grouping helpers, with no ORM access -- shared
by EventIndexPage, the calendar and UnionPage.

Design rationale/history: docs/claude_context/event_models.md"""

from datetime import date, timedelta
from itertools import groupby


def group_events_by_month(events_list):
    """[{"month": date(...), "events": [...]}, ...], consumed by
    events/partials/event_month_groups.html (EventIndexPage's own upcoming/
    past listings, and UnionPage's). groupby only merges *consecutive*
    equal keys -- safe since events_list is expected to already be sorted
    by event_date (ascending for upcoming, reversed for past)."""
    return [
        {"month": month, "events": list(month_events)}
        for month, month_events in groupby(
            events_list, key=lambda event: event.event_date.replace(day=1)
        )
    ]


def week_bounds(day):
    """(monday, sunday) of the calendar week containing `day`."""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def semester_bounds(day):
    """(start, end) of the semester containing `day` -- same Jan-Jun /
    Jul-Dec split EventIndexPage.get_context already uses for its
    is_spring_semester label, generalized into an actual date range."""
    if day.month <= 6:
        return date(day.year, 1, 1), date(day.year, 6, 30)
    return date(day.year, 7, 1), date(day.year, 12, 31)


def group_events_by_day(events_list):
    """[{"date": date(...), "time_tag": "today"|"tomorrow"|None,
    "events": [...]}, ...], consumed by the homepage events box.

    `time_tag` is taken from the group's first event, not recomputed from
    the date -- an event already in progress reports "today" even though
    the group is keyed by its start date. See
    docs/claude_context/home_eventsbox.md.
    """
    return [
        {
            "date": day,
            "time_tag": day_events[0].time_tag,
            "events": day_events,
        }
        for day, day_events in (
            (day, list(group))
            for day, group in groupby(events_list, key=lambda event: event.event_date)
        )
    ]
