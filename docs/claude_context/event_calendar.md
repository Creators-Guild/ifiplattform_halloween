# event_calendar.css / event_calendar_legend.css — design rationale

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/event/event_calendar.css, ifiplatform/apps/ifi_home_app/static/css/06_components/event/event_calendar_legend.css

Covers `ifi_home_app/static/css/06_components/event/event_calendar.css` —
the week/day calendar grid shared by a single event page's sub-events
(`event_page.html`) and a union page's own weekly calendar
(`union_page.html`/`union_calendar_panel.html`, via `union_calendar.js`) —
and `event_calendar_legend.css` (the color legend above it).

## `.union-calendar-nav`: fixed-width columns, not flex/1fr centering

The union calendar reuses `events/partials/event_calendar_grid.html` and
the `.event-calendar-*` rules as-is, but navigates via `union_calendar.js`
swapping the panel in place (not `event_calendar.js`'s day pager), so it
has its own always-visible nav row instead of `.event-calendar-pager`.

The label's text (a date range) varies in width week to week. Flex +
`justify-content: center`, or a `1fr` center column, would shift the
prev/next arrows along with it — `1fr` especially, since it'd stretch to
the full width of `.union-calendar-section`, planting the arrows way out
at its edges, far from the label they control. `1.5rem 19rem 1.5rem` fixed
columns keep the arrows both close to the label and pinned in place
regardless of which week/locale is showing — `19rem` comfortably fits the
longest realistic label with room to spare (measured: nb's
"1. september - 7. september 2026" is ~17.6rem). `width: fit-content` +
`margin: auto` centers this fixed-size block within the wider section
instead of stretching to it. Under the `45rem` breakpoint the middle
column shrinks to `13rem` (19rem is too wide for a phone) — still fixed,
not `auto`/`1fr`, for the same don't-move-the-arrows reason.

## Hour height: `--ec-hour-height` / `--ec-hours`

`--ec-hour-height` on `.event-calendar` is the one place each hour's
height is set. `.event-calendar-hours` and `.event-calendar-day` both
compute `height: calc(var(--ec-hours) * var(--ec-hour-height))`
(`--ec-hours` = `hour_count` from `EventPage.calendar_days`, set inline),
and the day column's gridline gradient repeats every `--ec-hour-height`,
so a block's top/height percentages (relative to the column) land on the
right gridlines. Never hardcode an hour height elsewhere — overriding the
one custom property is how every variant resizes the whole grid:

- `3.75rem` — base `.event-calendar` default (a single event's narrower
  hour span).
- `2.75rem` — `.union-calendar-section .event-calendar`.
  `UnionPage.get_context` fixes a union's calendar to one hour range for
  its whole semester (`models/event/calendar_layout.py`'s `hour_range_for_events`,
  derived from that union's earliest/latest timed event that semester,
  `9:00`-`01:00` fallback) rather than each week resizing around its own
  events; at `3.75rem` that semester-wide (often mostly empty) range would
  be too tall.
- `2.25rem` — under `45rem`, so a whole day fits closer to one phone
  screen instead of needing a long vertical scroll.

Hourly gridlines are a `repeating-linear-gradient` background on
`.event-calendar-day`, not one element per hour — they're purely
decorative; `.event-calendar-hour-label`s are the only positioned hour
elements. The label's `transform: translateY(-0.5em)` centers its text
*on* the gridline it marks (its `top` is the line's own position) instead
of hanging below it like a caption.

## `.event-calendar`'s background and `--ec-bg`

`background-color: #e5e5e5` on `.event-calendar` was flagged as a
temporary test color "per request" — expect it to change. `--ec-bg` must
always hold the same value as that `background-color`: under `45rem` the
sticky hour rail (`.event-calendar-hours`, `.event-calendar-header-spacer`,
`position: sticky; left: 0`) paints `background-color: var(--ec-bg)` so it
masks day columns scrolling underneath it, and `background-color` isn't an
inherited property, so the rail can't just pick it up from its ancestor.
Change one, change both. The mobile full-screen modal overrides `--ec-bg`
to `var(--color-bg-dark)` for the same masking reason against its dark
background.

## Single-event page: the calendar's own width

Sits outside `.event-page-prose`'s 50rem reading column on purpose
(`event_layout.css`, see `event_page.md`) and left-aligned, using the
page's full given width (`.maincontent`'s) with no cap — a 5-day grid
needs the room, unlike prose. Narrower screens just get more cramped
columns until the `45rem` mobile treatment takes over.

## `.event-calendar-block` vs `.event-calendar-block-inner`: why two boxes

`.event-calendar-block` is purely a positioning box — `top`/`height`/
`left`/`width` (inline style) are `EventPage.calendar_days`' computed
percentages, unmodified by anything else here. It deliberately holds none
of the visible styling itself: `margin` doesn't actually shrink an
absolutely-positioned box's own width/height (those stay exactly as
specified), it only shifts the box within the space `top`/`left`/`width`/
`height` already claim — a margin here would open a gap on the top/left
edges while the bottom/right edges keep overflowing past their gridline
by the same amount. `inset: 3px` on the nested absolutely-positioned
`.event-calendar-block-inner` is the one that actually resolves against
this box's real, already-computed pixel size, so it can shrink evenly on
all four sides — `position: absolute` on the outer box alone is enough
for it to be that inner child's containing block, no separate
`position: relative` needed. `box-sizing: border-box` on the inner box
keeps its 1px border inside that inset gap instead of growing the box.

Blocks use dark text (`--color-event-text`) on pastel backgrounds, not the
site-wide white-on-saturated `.event-type-badge` convention — that works
at badge scale but is too low-contrast at block size; the printed
schedule this view mirrors makes the same choice.

`.event-calendar-block--{blue,yellow,…}` suffixes are
`EventPage.calendar_color`'s choice values (blank falls back to
`_resolve_calendar_color`'s event_type mapping in `models/event/calendar_layout.py`).
`custom` has no rule here — its background comes from the block's inline
style (`calendar_color_custom`, freeform hex). These `--{color}` rules
must only ever set `background-color`: `event_calendar_legend.css`'s
`.event-calendar-legend-swatch` borrows the same classes for its color so
the legend and blocks can't drift apart, and any other property added to
a `--{color}` rule would leak onto the swatch.

The hover lift (`translateY(-2px)` on the inner box) is the same
convention as `.articlecard`; safe here because the block is absolutely
positioned and can't shift siblings.

## Touch: `.is-selected` two-tap select-then-navigate

On no-hover devices `event_calendar.js` makes the first tap on a block add
`.is-selected` and only the second tap navigate — in both the inline grid
and the modal's copy. `.is-selected` reuses the hover lift and also lets
`.event-calendar-block-inner` grow (`overflow: visible; height: auto;
bottom: auto; min-height: 100%`) so a clipped title/time shows in full;
`bottom: auto` is required alongside `height: auto`, since `inset: 3px`
would otherwise still pin the height. `.event-calendar-block-hint` is
always in the DOM (`event_calendar_grid.html`) and only shown under
`.is-selected` — it's what tells a first-time visitor a second tap is
needed.

## Mobile (`max-width: 45rem`): horizontal scroll, then paging

Must match `event_calendar.js`'s `MOBILE_QUERY` (`(max-width: 45rem)`).

Squeezing 5 day columns into phone width made blocks unreadable, so
`.event-calendar` scrolls horizontally instead: `.event-calendar-day`/
`-header-day` become `flex: 0 0 8rem` — the `flex-shrink: 0` is what
actually forces the overflow (the flex rows can no longer squeeze them).

`overflow-y: hidden` alongside `overflow-x: auto` on `.event-calendar` is
required, not decorative: with only `overflow-x` set, the spec computes
`overflow-y: visible` as `auto`, and on mobile Safari (with
`-webkit-overflow-scrolling: touch`) that captures vertical swipes
starting on the calendar into scrolling inside it instead of scrolling
the page. Nothing needs vertical clipping — the element is exactly
`--ec-hours` × `--ec-hour-height` tall.

`.event-calendar-controls` and `.event-calendar-pager--bottom` are
`display: none` unconditionally in the base rules and only shown inside
the `45rem` block. `--bottom` is a second prev/next pair below the grid
(`event_page.html`) so paging doesn't require scrolling back up;
`event_calendar.js` binds both copies and keeps their disabled state in
sync.

Single-day paging: `event_calendar.js` adds `.event-calendar--paged` to
the *inline* grid only, and `--current` to the current day's header/
column. The hide-other-days rules are scoped under `--paged` deliberately:
a JS-disabled browser never gets the class and so falls back to the
horizontal scroll instead of hiding every day, and the modal's grid copy
never gets it either, so it always shows the whole week.

## The "view whole week" modal

`position: fixed; inset: 0` and the color-mix backdrop for
`.event-calendar-modal` come from `06_components/shared/modal_base.css`,
shared by every full-screen modal; this file only adds z-index, flex
centering and `:not([hidden])` display. Close mechanics modeled on
`messageboard_modal.css`'s `.messageboard-modal`, but the content itself
is the full grid (`event_calendar_grid.html`), scrolled HORIZONTALLY
exactly like the grid's mobile fallback — with an explicitly visible
scrollbar (`scrollbar-width: auto` + `::-webkit-scrollbar` rules on
`.event-calendar-modal-scroll`) and edge fade hints, since an auto-hiding
native scrollbar is exactly the "not obvious it's scrollable" problem
this feature exists to fix. Not media-query-gated itself: only ever
opened from `.event-calendar-view-whole-week`, which is CSS-hidden
outside mobile.

`.event-calendar-modal-scroll .event-calendar`'s `width: max-content` lets
the row grow past the panel's own width instead of being squeezed back
down to fit it, which is what actually creates the horizontal overflow to
scroll — the `45rem` fixed per-day width rules already give the wanted
layout inside the modal; it just must never collapse to one day, which it
won't since this copy never receives `.event-calendar--paged`.

The fade hints (`.event-calendar-modal-fade-left`/`-right`) are direct
children of `.event-calendar-modal-panel` (not `.event-calendar-modal-
scroll`), so they stay fixed at the panel's edges regardless of scroll
position — same reasoning as `.messageboard-modal-fade` (see
`messageboard.md`). Visibility (`.is-visible`) is toggled by
`event_calendar.js`'s `updateFades()` from `scrollLeft`/`scrollWidth`/
`clientWidth`, re-checked on scroll, resize, and modal open.

`max-height` is declared twice (`85vh` then `85dvh`) as a fallback pair —
the later `dvh` wins where supported (see `messageboard.md` for why `dvh`).
Note that the mobile block's `.event-calendar-modal-panel` and
`.event-calendar-modal-scroll` declare them in the *opposite* order
(`100dvh` then `100vh`), so `vh` always wins there — likely unintended;
check before "fixing" either direction.

## Mobile full-screen modal takeover

True full-screen takeover on phones for the "view whole week" modal,
rather than the smaller centered card it uses above the `45rem`
breakpoint. At 100% width/height the panel IS the whole visible modal
(the dark `.event-calendar-modal` backdrop behind it has no edges left
showing), so its own background has to carry the "dark, see-through to
the page behind" look itself — the desktop card's opaque `--color-bg`
would otherwise hide the site completely. Text/backgrounds that assumed a
light card underneath (day headers, hour labels, the sticky hour rail via
`--ec-bg`, gridlines, the close button) are overridden alongside it so
they stay legible against dark.

## `event_calendar_legend.css`

`.event-calendar-legend` renders `EventPage.calendar_legend`
(`event_page.html`) — only output at all when it has entries, so there's
no separate show/hide toggle. Swatch colors come from the borrowed
`.event-calendar-block--{color}` classes (see above).
