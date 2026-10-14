# event_layout.css — design rationale

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/event_layout.css

Covers `ifi_home_app/static/css/05_objects/event_layout.css` — the single
event page's layout (`event_page.html`). The events index uses its own
wrapper (`.event-index-page`), so none of this affects it.

## Prose column vs. full-width sections

`.event-page` only centers text; it is deliberately *not* width-capped.
The reading-width cap lives on `.event-page-prose` (`max-width: 50rem`),
which wraps only title/meta/tags/intro. The sub-events calendar
(`.event-calendar`, see `event_calendar.md`) and Involved Unions
(`.event-union-list`) sit *outside* that wrapper in `event_page.html` on
purpose, so they get the page's full width. Moving them inside
`.event-page-prose`, or putting a `max-width` back on `.event-page`, would
squeeze a multi-day calendar into a paragraph-width column.

## Card grids

- `.event-location-articles-grid` (`EventPage.location_article_pages`)
  reuses `.articlecard` (`article_card.css`) as-is. `article_card.css`'s
  sizing assumes a grid/list container that controls width, so each card
  is capped here (`flex: 0 1 18rem; max-width: 18rem`) — otherwise a lone
  card would stretch across the whole section.
- `.event-union-list` reuses `.union-card` (`union_card.css`) and has no
  `max-width` of its own: each `.union-card` is already capped
  (`max-width: 14rem`), so the list just wraps more cards per row rather
  than leaving the page's width empty beside a narrow column.
