# Events

Last updated: 2026-10-09

How events work on the site: the event pages, the event list and the
sub-event calendar, the events box on the home page, and the sync that
copies events from Peoply. Read [overview.md](../overview.md) first for the
page tree, and [frontend.md](../frontend.md) for how templates and CSS are
loaded. Student unions, which own the Peoply link, are in
[unions_and_tools.md](unions_and_tools.md). Menus, including the "Events"
menu entries, are in [menus.md](menus.md).

## What it is

- **Visitors** see an events overview ("Arrangementer"), one page per event,
  and a "Happening at Ifi" box on the home page. A big event such as
  Fadderuke can have sub-events, shown in a week calendar on its page.
- **Editors** can write events by hand in the Wagtail admin. Most events,
  though, come from [Peoply](https://peoply.app), the event platform the
  student unions use. A sync copies them in several times a day.
- **Staff** see a "Sync Peoply now" button on the event pages and the home
  page, for when they can't wait for the next scheduled sync.

## Where events sit in the page tree

```
ArticleIndexPage (hub)
└── EventIndexPage          the events overview, one per language
    └── EventPage           an event
        └── EventPage       a sub-event (only one level deep)
```

- `EventIndexPage` may only have `EventPage` children.
- `EventPage` may sit under an `EventIndexPage` or another `EventPage`.
- `EventPage.can_create_at` stops a sub-event from having sub-events of
  its own. `subpage_types` can only limit page *types*, not depth, so this
  check is done in code.
- The sync always creates events directly under the first live nb
  `EventIndexPage`. It never creates sub-events.

## Models

All in `apps/ifi_home_app/models/event/` (`pages.py` for the page models,
`peoply.py` for the sync models).

### EventIndexPage

Has only an `intro` rich text field. Its `get_context` loads its live
child events in the active language and splits them:

- **Upcoming:** not archived, and the last day (`end_date`, or
  `event_date` if there is none) is today or later. A week-long event is
  still upcoming on day 2.
- **Past:** archived, or the last day is before today. Shown newest month
  first.

Both lists are grouped by month with `group_events_by_month`. Only direct
children are listed, so sub-events never show up here.

### EventPage

One model covers single events, multi-day events and deadlines. They only
differ in which fields are filled in.

| Field | What it does |
| --- | --- |
| `event_type` | Social, deadline, academic, company presentation or other. Sets the badge and the default calendar color |
| `event_date`, `event_time` | Start day and start time. No time means "all day" |
| `event_end_time` | End time, used to size the block in the calendar |
| `end_date` | Last day of a multi-day event |
| `location`, `location_map_links` | Place name, and one or more links to a map |
| `location_articles` | Links to articles about the place, shown as cards |
| `intro` | The description |
| `related_unions` | Unions involved, each with a role: host, collaborator or contributor |
| `show_on_homepage` | Whether the event may appear in the home page box. On by default |
| `is_highlighted` | For a sub-event: show it in the parent's dropdown in the home page box |
| `calendar_color`, `calendar_color_custom` | Override the block color in the parent's calendar |
| `calendar_legend` | On a parent event: explains what each calendar color means |
| `peoply_url`, `signup_url` | Link to the Peoply page, and to an outside sign-up form |
| `info_tags` | Free-text tags such as "Food served" |
| `external_source`, `external_uid` | Set by the sync: `"peoply"` and Peoply's event id. Empty on hand-made events |
| `is_archived` | Removed from Peoply, but kept under past events |

Useful properties on `EventPage`:

| Property | Returns |
| --- | --- |
| `is_happening_now` | True on every day from `event_date` to `end_date` |
| `time_tag` | `"today"`, `"tomorrow"` or `None` |
| `sub_events` | Live child events, in date and time order |
| `all_related_unions` | This event's unions plus every sub-event's, one entry per union. A sub-event's "host" counts as "collaborator" for the parent |
| `highlighted_sub_events` | Today's sub-events if there are any, otherwise the ones marked `is_highlighted` |
| `calendar_days` | The sub-events laid out for the week calendar (see below) |
| `localized_location_articles` | The linked articles in the active language |

Why `.localized`? A page picked in a StreamField (a `PageChooserBlock`)
is not translated by wagtail-localize. It keeps pointing to the Norwegian
page. So templates call `.localized` on unions and articles, or the
English site would link to Norwegian pages.

### Peoply bookkeeping models

| Model | One row per | Who writes it |
| --- | --- | --- |
| `PeoplySyncState` | Only one row. Holds the time of the last successful sync | `sync_peoply_events` |
| `PeoplySyncLog` | Click on "Sync Peoply now": who and when | The sync button view |
| `PeoplyRemovedEvent` | Synced event that disappeared from Peoply | `sync_peoply_events`, then a superuser in Django admin |
| `PeoplyUnionMismatch` (and four proxy models) | Problem linking a union to Peoply | `check_peoply_union_matches` |

All of them are superuser-only in the Django admin (`admin.py`). The union
mismatch logs belong to unions, see [unions_and_tools.md](unions_and_tools.md).

## The Peoply sync

### What starts it

| Trigger | How |
| --- | --- |
| systemd timer on the server | `deploy/systemd/sync-peoply-events.timer` runs `sync_peoply_events` at 00, 06, 12 and 18 every day, and at 14 and 16 on weekdays. `Persistent=true` catches up a run missed while the server was off |
| "Sync Peoply now" button | Staff only. Posts to `/api/peoply/force-sync/` (`views/event_views.py`), which logs a `PeoplySyncLog` row and runs the command |
| By hand | `python manage.py sync_peoply_events`, see [management_commands.md](../../operations/management_commands.md) for the options |

How the timer is installed and checked is in
[prod_server.md](../../operations/prod_server.md). A guide to all background
jobs is planned as `shared/background_jobs.md`.

### What it does, step by step

`apps/ifi_home_app/management/commands/sync_peoply_events.py`:

```
live UnionPages with a peoply_organization_id
        │   one fetch per union (nb and en copies share the id)
        ▼
peoply_api.get_events(org_id, after)   ← all unions fetched before anything is written
        │
        ├─ new event?          create an EventPage under the nb EventIndexPage, publish it
        ├─ known, changed?     overwrite the Peoply fields, publish a new revision
        ├─ known, unchanged?   do nothing (no new revision)
        └─ back after removal? republish it, mark the removal log "reappeared"
        │
known upcoming events Peoply no longer returns  →  unpublish, log a PeoplyRemovedEvent
        │
sync_locale_trees  →  clear the site-root-paths cache  →  PeoplySyncState.touch()
        │
check_peoply_union_matches  (a report only; its failure does not undo the sync)
```

1. **Pick unions.** Every live `UnionPage` with a `peoply_organization_id`.
   How that id gets set is in [unions_and_tools.md](unions_and_tools.md).
2. **Fetch.** `integrations/peoply_api.py` calls `GET /events` on
   `api.peoply.app` with `organizationId` and `afterDate`, 500 events per
   page, 10 second timeout. `afterDate` is now, or the `--after` date.
   An error response raises an exception, so the run stops before it has
   changed anything.
3. **Match.** An event is found again by `external_source="peoply"` and
   `external_uid` (Peoply's event id), in the nb locale.
4. **Convert.** Peoply times are UTC. They are converted to Oslo time
   before being split into date and time. The description is plain text and
   is turned into HTML paragraphs. The location is `freeformAddress`, or
   `locationName`.
5. **End time or end date.** If the event ends the same day, or before
   06:00 the next day, the end goes in `event_end_time`. Otherwise it goes
   in `end_date` and the event counts as multi-day. Without the 06:00 rule,
   a party ending at 01:00 would show as "happening now" all the next day.
6. **Create.** A new event gets a free slug, `event_type` "company" if the
   title contains "Bedriftspresentasjon" and "social" otherwise, and the
   union as host in `related_unions`. It is published at once.
7. **Hide removed events.** A synced event that Peoply no longer returns is
   unpublished (its English alias too) and logged, but only if it starts
   after the `afterDate` and its host union was synced in this run. Past
   events are never hidden, because Peoply never returns them.
8. **English copies.** Pages made in code skip the Wagtail admin hook
   that creates the English alias. So the command runs `sync_locale_trees`,
   which creates the missing aliases. New events are not translated; the
   English page shows the Norwegian text until someone translates it.
9. **Clear the cache.** Creating many pages in code does not clear Wagtail's
   site-root-paths cache. A stale cache once made links render as
   `href="None"`, so the command clears it.

### Who owns which field

The sync overwrites these fields (`PEOPLY_SYNCED_FIELDS`) every time they
change on Peoply:

`title`, `event_date`, `event_time`, `event_end_time`, `end_date`,
`location`, `intro`, `peoply_url`, `signup_url`

On a Peoply event these fields are locked in the Wagtail admin
(`EventPageForm`), with the help text "Synced from Peoply -- edit it on
Peoply instead". Fix them on Peoply, not here.

Everything else belongs to editors. The sync sets `event_type` and
`related_unions` once, when it creates the page, and never touches them
again. Colors, tags, map links, location articles, `show_on_homepage` and
`is_highlighted` are never set by the sync. The slug also stays the same
when the title changes.

`signup_url` is only filled when Peoply's event uses an outside sign-up
form. When it is empty on a Peoply event, the event page shows a
"Signup at Peoply" button instead.

If an editor unpublishes a Peoply event, the sync leaves it unpublished.

### When an event disappears from Peoply

The page is unpublished and a `PeoplyRemovedEvent` row is opened. A
superuser then picks one of two actions in the Django admin, under "Events
removed from Peoply":

- **Archive:** republishes the page with `is_archived=True`. It is listed
  only under past events, shows "This event is no longer listed on Peoply",
  and is left out of the home page and union pages.
- **Delete:** deletes the page in every language for good.

If the event comes back on Peoply first, the next sync republishes it and
marks the row "reappeared".

### When the sync fails

- **On the server:** run `journalctl -u sync-peoply-events.service` to see
  the output. The last line of a good run is
  `Done: N created, N updated, N unchanged, N restored, N hidden`.
- **Peoply is down or slow:** the fetch raises an error and the run stops
  before writing anything. The next timer run tries again. The
  "last synced" time on event pages will be older than usual.
- **"No live nb EventIndexPage found":** the events overview page is
  missing or unpublished in Norwegian.
- **A union's events never appear:** its `peoply_organization_id` is empty or
  wrong. The report from `check_peoply_union_matches` at the end of the run
  lists stale links.
- **The sync button gives an error page:** the button runs the whole sync
  inside the web request, so a Peoply error shows up as a server error. The
  click is still logged.

## The event page and its calendar

Template: `templates/events/event_page.html`. It shows the type badge,
date, time, place, tags, the sign-up buttons, the description, location
article cards, the sub-events and the involved unions (hosts in their own
row).

If the event has sub-events, `calendar_days` lays them out as a week
calendar (`build_calendar_days` in `models/event/calendar_layout.py`):

- One column per day that has a timed sub-event.
- The hour axis only spans the sub-events' own hours.
- Sub-events at the same time are placed side by side.
- Sub-events without a time can't go on a grid, so they are listed below it.
- A block's color is `calendar_color` if set, otherwise it comes from
  `event_type`.

The grid itself is `templates/events/partials/event_calendar_grid.html`,
which union pages reuse for their own week calendar. `static/js/event_calendar.js`
adds the mobile parts: one day at a time with arrows and swipe, tap once to
select a block and again to open it, and a "View whole week" pop-up.

## The event list

`templates/events/event_index_page.html` shows the semester (January to
June is spring), the upcoming events by month, and past events in a
collapsed `<details>`. Each month is rendered by
`templates/events/partials/event_month_groups.html`, which union pages
also use.

## The home page events box

The home page is a Django view, not a Wagtail page.
`views/home_views.py` (`main_view`) picks up to 6 events:

- live children of the active language's `EventIndexPage`
- `show_on_homepage` on, not archived
- still running today or later, in date and time order

`home_views` groups them by day with `group_events_by_day()`
(`models/event/dates.py`); `templates/home/partials/eventsbox/eventsbox.html`
renders the groups, with "Today" or "Tomorrow" in the heading when it fits.
`eventsbox/event.html` renders one event: time (or end date, or
"All day"), badge, title, a "Click to see calendar" link when it has timed
sub-events, up to two union tags plus a "+N" expander, and a sub-event
dropdown with `highlighted_sub_events`. The expanders are native
`<details>`, with no JavaScript. Below 72rem the CSS hides every day after
the third.

## Shared pieces

| Piece | Where | Used on |
| --- | --- | --- |
| "data from peoply" badge | `templates/events/partials/peoply_badge.html` | event list, calendar blocks, home box, and with the last sync time on the event page |
| "Sync Peoply now" button | `templates/events/partials/peoply_sync_button.html` + `static/js/peoply_sync_button.js` | event page, events overview, home box (staff only) |
| CSS | `static/css/05_objects/event_layout.css`, `static/css/06_components/event/`, `static/css/06_components/home/home_eventsbox*.css` | loaded through `templates/css_links/event.html`, `event_index.html`, `home_index.html` |

The button's script only disables it for 5 seconds after a click, to stop
double clicks. There is no real rate limit on the server; `PeoplySyncLog`
shows who clicked.

## Where to change things

| If you want to… | Look at |
| --- | --- |
| Add or change an event field | `EventPage` in `models/event/pages.py`, then a migration |
| Let editors change a field the sync owns, or the other way round | `PEOPLY_SYNCED_FIELDS` in `models/event/peoply.py`, and `_peoply_fields` in `sync_peoply_events.py` |
| Change how Peoply data is turned into fields | `_peoply_fields`, `_infer_event_type` in `management/commands/sync_peoply_events.py` |
| Change the Peoply API calls | `integrations/peoply_api.py` |
| Change when the sync runs | `deploy/systemd/sync-peoply-events.timer` |
| Change what counts as upcoming or past | `EventIndexPage.get_context` |
| Change which events the home box shows | `main_view` in `views/home_views.py` |
| Change the calendar layout or colors | `build_calendar_days`, `_resolve_calendar_color` in `models/event/calendar_layout.py` |
| Change how an event page looks | `templates/events/event_page.html`, `static/css/06_components/event/` |
| Handle events removed from Peoply | `PeoplyRemovedEventAdmin` in `admin.py` |
| Test the sync | `tests/test_peoply_sync.py` (it mocks the Peoply API) |

All paths are in `apps/ifi_home_app/`, except `deploy/`, which is at the repo root.

## Gotchas

- **Don't edit synced fields in code or the database.** The next sync
  overwrites them from Peoply.
- **Time zones.** `settings.TIME_ZONE` is UTC, but event times are Oslo
  time. The sync and the last-sync badge use `SITE_TIMEZONE`
  (Europe/Oslo) on purpose.
- **Calendar percentages are strings.** `_pct` returns text like `"12.3456"`
  on purpose. A float would be printed as `12,3456` in Norwegian, which is not
  valid CSS, and every block would lose its position.
- **Locally, the sync calls the real Peoply API.** `seed_dev_data` only
  links two unions to Peoply, so a local run stays small.
