"""Week-calendar layout -- turns a set of events into positioned,
colored blocks for the calendar grid. Pure functions: no ORM, no
models imported.

Design rationale/history: docs/claude_context/event_models.md"""


def _event_start_minutes(event):
    return event.event_time.hour * 60 + event.event_time.minute


def _event_end_minutes(event):
    if not event.event_end_time:
        return _event_start_minutes(event) + 60
    end = event.event_end_time.hour * 60 + event.event_end_time.minute
    if end <= _event_start_minutes(event):
        # Wraps past midnight (e.g. 22:00-00:30): ending earlier than it
        # starts means it's actually the next day. +24h puts it in the
        # small-hours tail of the day instead of producing a negative-height
        # block.
        end += 24 * 60
    return end


MIN_CALENDAR_HOUR_SPAN = 4


def hour_range_for_events(events):
    """(hour_start, hour_end) spanning every timed event in `events`, or
    None if none of them are timed. Used to fix UnionPage's calendar to one
    hour axis for its whole semester (see UnionPage.get_context) rather
    than recomputing it -- and so potentially reshuffling it -- week to
    week."""
    timed = [e for e in events if e.event_time]
    if not timed:
        return None
    hour_start = min(_event_start_minutes(e) for e in timed) // 60
    hour_end = max(-(-_event_end_minutes(e) // 60) for e in timed)  # ceil-div
    hour_end = max(hour_end, hour_start + 1)

    # A union with only one or two events close together (e.g. every
    # meeting at 16:00-18:00) would otherwise get a cramped 1-2 hour-tall
    # grid -- pad out to a sane minimum, spread before/after evenly so
    # those events land roughly centered rather than pinned to the top.
    span = hour_end - hour_start
    if span < MIN_CALENDAR_HOUR_SPAN:
        deficit = MIN_CALENDAR_HOUR_SPAN - span
        extend_before = min(deficit // 2, hour_start)  # never push below 0
        hour_start -= extend_before
        hour_end += deficit - extend_before

    return hour_start, hour_end


def build_calendar_days(events, day_range=None, hour_range=None):
    """Lays `events` out for a week-calendar view -- see
    docs/claude_context/event_models.md for the full layout algorithm.

    `day_range`, if given, is an explicit list of dates (e.g. a fixed
    Mon-Sun week) to always produce a column for, even ones with no events
    -- without it, only dates that actually have a timed event get a
    column (EventPage.calendar_days' original behavior).

    `hour_range`, if given, is an explicit (hour_start, hour_end) to use
    for the hour axis instead of deriving it from `events` -- UnionPage
    passes one fixed range (see hour_range_for_events) covering its whole
    semester, so every week renders the same hours rather than resizing
    around whichever events happen to fall in that particular week."""
    timed = [e for e in events if e.event_time]
    untimed = [e for e in events if not e.event_time]

    if not timed and day_range is None and hour_range is None:
        return {
            "hour_start": 0,
            "hour_end": 0,
            "hour_marks": [],
            "hour_count": 0,
            "days": [],
            "untimed": untimed,
        }

    start_minutes = _event_start_minutes
    end_minutes = _event_end_minutes

    if hour_range is not None:
        hour_start, hour_end = hour_range
    elif day_range is not None:
        hour_start, hour_end = 9, 25  # fallback: 9:00 to 01:00 the next day
    else:
        # timed is non-empty here -- the only other case (day_range is
        # None and not timed) already returned above.
        hour_start = min(start_minutes(e) for e in timed) // 60
        hour_end = max(-(-end_minutes(e) // 60) for e in timed)  # ceil-div
        hour_end = max(hour_end, hour_start + 1)
    total_minutes = (hour_end - hour_start) * 60

    days = []
    for day_date in (
        day_range if day_range is not None else sorted({e.event_date for e in timed})
    ):
        day_events = sorted(
            (e for e in timed if e.event_date == day_date),
            key=lambda e: (start_minutes(e), end_minutes(e)),
        )
        blocks = []
        for cluster in _cluster_overlapping(day_events, start_minutes, end_minutes):
            columns = _assign_columns(cluster, start_minutes, end_minutes)
            for event in cluster:
                col, col_count = columns[event]
                color_key, color_hex = _resolve_calendar_color(event)
                blocks.append(
                    {
                        "event": event,
                        "top_pct": _pct(
                            start_minutes(event) - hour_start * 60, total_minutes
                        ),
                        "height_pct": _pct(
                            end_minutes(event) - start_minutes(event), total_minutes
                        ),
                        "left_pct": _pct(col, col_count),
                        "width_pct": _pct(1, col_count),
                        "color_key": color_key,
                        "color_hex": color_hex,
                    }
                )
        days.append({"date": day_date, "events": blocks})

    hour_marks = [
        # h % 24 for display only -- top_pct still needs the raw,
        # un-wrapped h to land in the right place past the 24:00 mark.
        {"hour": h % 24, "top_pct": _pct(h * 60 - hour_start * 60, total_minutes)}
        for h in range(hour_start, hour_end + 1)
    ]

    return {
        "hour_start": hour_start,
        "hour_end": hour_end,
        "hour_marks": hour_marks,
        "hour_count": hour_end - hour_start,
        "days": days,
        "untimed": untimed,
    }


_AUTO_CALENDAR_COLOR_BY_EVENT_TYPE = {
    "academic": "blue",
    "deadline": "pink",
    "company": "purple",
    "social": "orange",
    "other": "orange",
}


def _resolve_calendar_color(event):
    """The (color_key, custom_hex) this event's calendar block renders with."""
    color = event.calendar_color or _AUTO_CALENDAR_COLOR_BY_EVENT_TYPE.get(
        event.event_type, "orange"
    )
    if color == "custom" and event.calendar_color_custom:
        return "custom", event.calendar_color_custom
    return color, None


def _pct(numerator, denominator):
    # Plain string, not a float -- Django's locale-aware {{ }} rendering
    # would break this inline style="...%" value. See
    # docs/claude_context/event_models.md before changing this.
    return f"{numerator / denominator * 100:.4f}"


def _cluster_overlapping(events, start_minutes, end_minutes):
    """Partitions start-time-sorted `events` into clusters of transitively
    overlapping events. See docs/claude_context/event_models.md."""
    clusters = []
    current = []
    current_max_end = None
    for event in events:
        s = start_minutes(event)
        if current and s >= current_max_end:
            clusters.append(current)
            current = []
            current_max_end = None
        current.append(event)
        e = end_minutes(event)
        current_max_end = e if current_max_end is None else max(current_max_end, e)
    if current:
        clusters.append(current)
    return clusters


def _assign_columns(cluster, start_minutes, end_minutes):
    """Greedy interval-graph coloring within one cluster of overlapping
    events. See docs/claude_context/event_models.md."""
    columns_end = []
    column_of = {}
    for event in cluster:
        s, e = start_minutes(event), end_minutes(event)
        col = next(
            (i for i, end in enumerate(columns_end) if end <= s), len(columns_end)
        )
        if col == len(columns_end):
            columns_end.append(e)
        else:
            columns_end[col] = e
        column_of[event] = col
    column_count = len(columns_end)
    return {event: (col, column_count) for event, col in column_of.items()}
