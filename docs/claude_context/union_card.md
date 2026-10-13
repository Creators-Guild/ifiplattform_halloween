# union_card.css — design history

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/cards/union_card.css

Covers `ifi_home_app/static/css/06_components/cards/union_card.css` (union
listing card, `studentunion_category_page.html`, also used on event pages
and as an article body block). The `height: 100%`, `.body-union-card`
`--card-width`/`--card-height`, mobile `overflow: visible` and
`overflow-wrap` patterns are shared with the other cards — see `cards.md`.

## `max-width: 14rem` on `.union-card`

Looks redundant next to `flex: 0 1 14rem` (flex-grow is already 0), but
flex-basis is only a starting size, not a ceiling. In some containers with
lots of spare row space (e.g. `.event-union-list` on a wide screen) the
card could still stretch past 14rem. Keep it.

## Why the mobile breakpoint is 45rem, not 480px

`45rem`, not the `480px` this used to be pinned to — matches the
breakpoint every other mobile treatment on a page `union-card` can appear
on already uses (`event_calendar.css`'s calendar/day-paging,
`article_list_toggle.js`, `dropdown_menu.js`, ...). At the old, narrower
`480px`, a page like an event's "Involved Unions" section
(`event_page.html`) would already be showing its *other* content in
mobile layout well before `union-card` followed suit — e.g. at 600-700px
wide, the week-calendar above it had already switched to single-day
mobile view while these cards were still sitting in full desktop grid
mode right below it, visibly inconsistent on the same page.

## Mobile compact row

Inside the 45rem query `.union-card` becomes a horizontal row with a
2.75rem logo and less padding, in every context. The stacked layout's 5rem
logo plus 1.5rem padding all round made it the biggest space user of the
four card types on a narrow screen.
