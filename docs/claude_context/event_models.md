# models/event/ — design notes

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/models/event/

Context for future Claude sessions. Not a human-facing doc.

Kept at this filename after the package split: the module docstrings in
`models/event/*.py` all point here, as do several other docs.

## Layout

Was one 899-line `models/event_models.py`; now a package:

| module | holds |
|---|---|
| `constants.py` | `SITE_TIMEZONE`, `EVENT_TYPE_CHOICES`, `EVENT_CALENDAR_COLOR_CHOICES` |
| `blocks.py` | the StreamField blocks `EventPage` uses |
| `pages.py` | `EventPageTag`, `EventPageForm`, `EventIndexPage`, `EventPage` |
| `peoply.py` | the Peoply sync-state/mismatch/removed-event models |
| `calendar_layout.py` | week-grid layout; pure functions, imports nothing |
| `dates.py` | `week_bounds`, `semester_bounds`, `group_events_by_month`; no ORM |
| `queries.py` | `upcoming_events_for_union`, `events_for_union_between` |

`__init__.py` deliberately imports nothing (same as `models/article/`), so
that importing e.g. `event.calendar_layout` doesn't drag in the article
models `pages.py` depends on. Model registration is done by
`models/__init__.py`, which imports both `event.pages` and `event.peoply` —
without that second import Django would stop seeing the Peoply models and
`makemigrations` would propose dropping their tables.

## Shape

`EventIndexPage -> EventPage`, same shape as `StudentUnionCategoryPage ->
UnionPage`. No `EditorModeMixin`/`BannerStyleMixin` on either page yet —
unlike `ArticlePage`/`CategoryPage`, there's no on-page style panel for
events to plug into; add it later if that changes. `TranslationWarningMixin`
is kept since these pages need nb/en translations like everything else on
this bilingual site.

`EventPage` covers dated events (Bar til bar), date ranges/week-long events
(Fadderuke, via `end_date`), and deadlines (Frist for funk-oppmelding)
through one shape rather than separate models — they only differ in which
fields are filled in. An `EventPage` may itself hold sub-events (e.g.
Fadderuke's daily events), capped at one level of nesting via
`can_create_at` (`parent_page_types`/`subpage_types` alone can only gate by
page *type*, not tree depth).

## SITE_TIMEZONE

`event_time`/`event_end_time` are plain (non-tz-aware) `TimeField`s, entered
and displayed as Oslo wall-clock with no conversion (this is an Ifi/UiO
site — that's where events happen). `settings.TIME_ZONE` is `"UTC"` though
(a storage/bookkeeping convention, not site-content), and nothing activates
a per-request timezone, so `timezone.localtime()` alone returns UTC
wall-clock, not Oslo's. `SITE_TIMEZONE = ZoneInfo("Europe/Oslo")` is needed
**only** where Oslo clock time matters: `sync_peoply_events` turning
Peoply's UTC times into `event_time`, and the last-sync badge
(`get_peoply_last_synced`). (`live_sub_events`, the one model-side clock
comparison, was removed as dead code.) Plain calendar-day comparisons elsewhere
(`is_happening_now`, `timezone.localdate()`) don't need it: UTC and Oslo
only ever disagree on which *day* it is within an hour or two of midnight,
an existing edge case elsewhere on the site too, not one this introduces.

## EVENT_CALENDAR_COLOR_CHOICES

Same "fixed palette + custom hex fallback" pattern as
`article/constants.py`'s `COLOR_CHOICES` (reusing `HEX_COLOR_VALIDATOR` from
there), but its own list: a pastel set matched to a printed program's own
color-coded legend, not the article box/border palette. `""` means "derive
one from `event_type`" (see `_resolve_calendar_color`), not a fixed default.

## upcoming_events_for_union

Filtered in Python, not `.filter()` — `related_unions` is a StreamField, not
a real relation. Compares by `translation_key` (not page id) so a union
tagged on an nb event still matches when viewing the en translation of that
union. Imported into `article/unions.py` via a **function-local** import to
avoid a circular import (this module imports from the `article_models` shim
at module level; `unions.py` importing this module at module level too
would cycle back).

## all_related_unions

Rolls up this event's own `related_unions` plus every sub-event's, deduped
by union keeping the highest-priority role (`host` > `collaborator` >
`contributor`). Without this, a parent event like Fadderuke — whose own
`related_unions` is typically empty, since a union only ever gets tagged on
the specific sub-event it's involved in — would show no involved unions at
all despite its sub-events listing plenty. `host` is only kept for a union
tagged host directly on *this* page; a union hosting one sub-event (e.g. CYB
running one quiz night) isn't the host of the whole week, so a sub-event's
own `host` role is capped down to `collaborator` once rolled up.

Each entry's `union` is resolved to `.localized.specific` here, once, rather
than leaving every template to remember it — same reasoning as
`localized_location_articles` below. Dedup still happens on the raw union's
`translation_key`, which is shared across locales, so resolving afterwards
doesn't change which unions survive. Without the `.localized` step an English
event page would link to and display the Norwegian union page, since a
`PageChooserBlock` inside a StreamField is deliberately not auto-translated
by wagtail-localize (see `handle_related_object_block()` in
`wagtail_localize/segments/extract.py`).

## host_unions / supporting_unions

`event_page.html` shows hosts in their own row above everyone else: the role
isn't just a label there, it's the point of splitting the section, so whoever
is actually running the event doesn't blend into the same wrapped grid as
every collaborator.

That split used to be done in the template, by looping `all_related_unions`
twice and filtering each pass on `role` — a workaround for `{% for %}` not
being able to filter or group. These two properties do it instead, so each
row loops a list that already contains exactly what it should show.

Each `all_related_unions` entry also carries `role_label`, read from
`UNION_ROLE_CHOICES` in `constants.py`. That list is the single source for
the role words: `event_union_block()` uses it for the editor's dropdown, and
the template just prints the label rather than redefining the same three
`{% trans %}` strings.

## signs_up_on_peoply

True for a Peoply-sourced event with no `signup_url`, which means Peoply's
own `registrationMode` was `"PEOPLY"` at sync time — `sync_peoply_events`
only ever fills `signup_url` for `"EXTERNAL"` mode. Registering then *is*
clicking through to Peoply, so `event_page.html` labels the button
"Signup at Peoply" rather than naming an external site.

## highlighted_sub_events

Today's sub-event(s) win whenever anything's scheduled today (e.g. day 3 of
Fadderuke), so the homepage always surfaces "what's on today" without an
editor re-flagging `is_highlighted` daily. Falls back to the
explicitly-curated `is_highlighted` set otherwise (before the event starts,
or on a day with nothing scheduled).

## calendar_days

Lays sub-events out for a week-calendar view: one column per distinct date,
blocks positioned/sized by minutes-since-midnight within a shared hour range
spanning just the sub-events themselves (not a fixed 00–24), fanned out
side by side within a day when times overlap (`_cluster_overlapping`/
`_assign_columns`) — the same layout a real calendar app uses for a
scheduling clash. Untimed sub-events can't be placed on a grid, so they come
back separately under `"untimed"` rather than being silently dropped.

- `_cluster_overlapping`: single sweep over start-time-sorted events;
  a new event starts a fresh cluster once every event in the current
  cluster has already ended by the time this one starts.
- `_assign_columns`: greedy interval-graph coloring — each event gets the
  lowest-numbered column whose most recent occupant already ended.
  `column_count` is per-cluster, not global, so an unclashed event still
  gets the full day-column width even if another cluster that day needed
  several columns.
- `_pct`: returns a plain `'12.34'` *string*, not a float — these values
  land in an inline `style="...%"` attribute. Django's own `{{ }}` number
  rendering is locale-aware; the active nb locale would render `7.69` as
  `"7,69"`, an invalid CSS decimal separator that silently drops the whole
  declaration and breaks every block's positioning. **Don't swap this back
  to a plain f-string float or a template filter** — it has to stay
  locale-independent string formatting.

## localized_location_articles

Resolves each linked ArticlePage to `.localized.specific` once, here,
rather than leaving every template to remember to do it. `PageChooserBlock`
references aren't auto-translated by wagtail-localize (see
`handle_related_object_block()` in `wagtail_localize/segments/extract.py`)
— applies the same way to a plain ForeignKey too, so there's no simpler
field type that sidesteps this.
