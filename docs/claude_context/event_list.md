# event_list.css / event_badges.css — design rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/event/event_badges.css, ifiplatform/apps/ifi_home_app/static/css/06_components/event/event_list.css

Covers `ifi_home_app/static/css/06_components/event/event_list.css` (the
events index listing, `event_index_page.html`) and `event_badges.css`
(badges/tags shared by the single event page, the events index, and the
homepage events box — see `home_eventsbox.md`).

## `.event-list-item`: `flex-wrap` + `min-width: 0` on the title

Both are overflow fixes, not decoration. Badge + a long title + a
`white-space: nowrap` date easily exceed a narrow card's width; without
`flex-wrap: wrap` on `.event-list-item` nothing can give way and the date
(or the whole row) overflows past the card border on mobile. With wrap,
the date drops to its own line when there's no room.

`.event-list-title { min-width: 0 }` is needed on top of that: flex items
default to `min-width: auto`, which stops a long unbroken title from
shrinking below its min-content width and forces the row to overflow
instead of wrapping the title's text.

## Past events

`.event-index-past` wraps `EventIndexPage.get_context`'s
`past_month_groups` in a native `<details>` (same pattern as
`account_settings.html`'s "Delete my account"), collapsed by default so
the page opens on what's upcoming.

## `event_badges.css`

- `.event-type-badge--*`: white-on-saturated category pills. The homepage
  "Happening now" label deliberately avoids `--color-accent` because it's
  `--social`'s color (see `home_eventsbox.md`).
- `.event-peoply-note` (`events/partials/peoply_badge.html`): plain
  provenance text, not a pill. `flex-basis: 100%` is what puts it on its
  own line inside the flex-wrap rows it lives in (`.event-list-item`,
  `.home-eventsbox-item`); `display: block` alone doesn't do that for a
  flex item. Where the parent isn't flex (`event_page.html`) the
  `flex-basis` is harmless and `display: block` handles it.
  `--compact` is for the week calendar's small blocks.
- `.event-tag` (`EventPage.info_tags`, plain django-taggit tags): same
  pill shape as `.event-type-badge` but muted/outlined, since flat tags
  carry no category to color by.
