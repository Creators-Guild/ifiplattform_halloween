# Homepage events box — design rationale

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/home/home_eventsbox.css, ifiplatform/apps/ifi_home_app/static/css/06_components/home/home_eventsbox_event.css

Covers the homepage "This month at Ifi" box:
`home/partials/eventsbox/eventsbox.html` (the list, empty state, "See all events",
staff Peoply button) and `home/partials/eventsbox/event.html` (one event
row, included per event), styled by
`ifi_home_app/static/css/06_components/home/home_eventsbox.css` (the box) and
`home_eventsbox_event.css` (the row). The box's outer sizing/placement lives in
`05_objects/home_layout.css` (see `home_layout.md`), including
`align-self: start` so the box is as tall as its content instead of stretching
to the column beside it.

It's a compact list, not the `newsbar_layout.css` card grid, because it sits in
a narrow column.

## No JavaScript

Both expanders are native `<details>`: the extra union tags and the sub-event
list. The box loads no script of its own (`peoply_sync_button.js` is staff-only
and belongs to the sync button). Don't reintroduce `dropdown_menu.js` here.

`.home-eventsbox-more-unions` is `display: contents` so its `<summary>` ("+N")
and the extra tags lay out as part of the same wrapping `.home-eventsbox-unions`
flex row instead of forming a block below it. Collapsed content still hides
correctly (verified with JS disabled). When testing, use `checkVisibility()`,
not `getBoundingClientRect()` — a collapsed `<details>` keeps a box.

## Row layout

Events are grouped by date with `{% regroup upcoming_events by event_date %}`
(`eventsbox.html`): one `.home-eventsbox-day` section per date, with an
`<h3>` heading and the day's events under it. A row
(`.home-eventsbox-item`) is a two-column grid: the start time on the left
(`.home-eventsbox-time`; "All day" when there is none, the end date for a
multi-day event) and `.home-eventsbox-body` on the right — badges, title,
calendar link, union tags, sub-events, one per line.

Earlier versions used a wrapping flex row where five children set
`flex-basis: 100%` to force their own line, plus a stretched-link overlay
(`.home-eventsbox-title-link::after`) that made the whole row clickable and
forced `position: relative; z-index: 1` on every interactive child. Both are
gone: only the title is a link.

Sub-event names wrap instead of being truncated, which removed the
`min-width: 0` chain the ellipsis needed on three levels.

## Time tag

`EventPage.time_tag` (`models/event/pages.py`) returns `"today"`, `"tomorrow"` or
`None` — at most one, nearest first. `"today"` reuses `is_happening_now`, so a
multi-day event running across today counts.

The pill sits on the day heading (`eventsbox.html`), taken from the first
event of the group, so it shows once per day rather than per row. Colours: today
filled green (`--color-success`), tomorrow filled turquoise.

There is no separate "Happening today" section any more — it repeated events
already listed below it, and `home_views.main_view` no longer builds
`happening_now_events`.

## Day grouping

`home_views` passes `upcoming_event_days` from `group_events_by_day()`
(`models/event/dates.py`), a sibling of the `group_events_by_month()` the
event index and union pages use. The template used to `{% regroup %}` the
flat list itself and then read `day.list.0.time_tag` — asking a group's first
event what day the group was.

**Known quirk, deliberately preserved:** `time_tag` reports `"today"` for an
event already in progress, while the groups are keyed by `event_date`. A
week-long event that began yesterday therefore renders a "Today" heading next
to yesterday's date. `group_events_by_day()` takes `time_tag` from the first
event rather than recomputing it from the date, specifically so the move out
of the template changed nothing. Worth fixing on its own, with a decision
about what such an event's heading should actually say.

## Template details

- **Union tags need no language handling.** Since the English overlay
  switch-over there is one (Norwegian) union page, and on /en/ its title
  and address are English by themselves (`translation_overlay.md`).
- **`event.all_related_unions`, not `event.related_unions`:** it rolls in every
  sub-event's unions too (docstring in `models/event/pages.py`). A week-long event
  like Fadderuke tags unions on its individual days, not on itself.
- **Only the first 2 union tags show**, the rest behind the `+N` expander. 2
  rather than 3 because this column is narrow on a phone.
- **`event.highlighted_sub_events`** is today's sub-events if any, else the
  curated `is_highlighted` set. With none, the row shows a plain count
  (`.home-eventsbox-subcount`) instead of the expander.
- **The calendar link** renders only when `event.calendar_days.days` exists — an
  untimed-only event has nothing at the `#event-calendar` anchor.
- **"See all events"**: `home_views.main_view` caps the box at 6 events, and
  `home_eventsbox.css` hides everything past the 3rd day below 72rem.

## Queries

`sub_events`, `all_related_unions`, `highlighted_sub_events` and `calendar_days`
are `@cached_property` (`models/event/pages.py`), so a row reading several of them
queries once per event rather than per access, and `sub_events.count` is free
once anything has iterated the queryset. Measured: the box costs ~19 EventPage
queries for 6 events; the homepage total (~236) is dominated by articles and
menus, so this box is not the place to optimise further.
