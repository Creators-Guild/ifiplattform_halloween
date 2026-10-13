# messageboard_slideshow.css / messageboard_modal.css — design rationale

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/home/messageboard_modal.css, ifiplatform/apps/ifi_home_app/static/css/06_components/home/messageboard_slideshow.css

Covers `ifi_home_app/static/css/06_components/home/messageboard_slideshow.css`
and `messageboard_modal.css` (`home/partials/messageboard/messageboard.html`,
`messageboard.js`).

## Why the mobile breakpoint is 72rem, and what changes there

`72rem`, not a narrower phone-only width — matches `home_layout.css`'s own
stacking breakpoint (the homepage grid goes single-column there, and
`.eventsbox_container` switches to its compact/collapsed mobile look at the
same width, `home_eventsbox.css`). Below that breakpoint the message
board sits directly above the events box in a single narrow column, so it
needs this compact treatment throughout that whole range, or the two
would visibly mismatch. `messageboard.js`'s own `MOBILE_QUERY` has to stay
in sync with this value by eye — no shared variable exists between plain
CSS files and JS.

Below 72rem: there isn't room for the centered dots and the right-aligned
signature to share a row, so both become normal flow instead of absolutely
positioned, stacking (signature, then the prev/dots/next controls row)
below the body text. Height switches from a fixed size to `auto` +
`max-height`: a short message stays compact, a long one grows up to the
cap. `.messageboard`'s padding also tightens since the arrows no longer
sit at its left/right edges.

## Desktop card (`messageboard_slideshow.css`)

- **Custom scrollbar**: `.messageboard-body` scrolls with its native
  scrollbar hidden; `.messageboard-scrollbar`/`-thumb` are a JS-driven
  drag handle (pointer events + `setPointerCapture` in `messageboard.js`).
  `touch-action: none` on both is required, or touch input would also pan
  the page during a drag. `.messageboard-body-wrap`'s `padding-bottom:
  1.75rem` and the scrollbar's `bottom: 1.75rem` reserve room for the
  absolutely-positioned dots/signature.
- **`.messageboard-controls { display: contents }`** at desktop size: the
  wrapper generates no box, so `.messageboard-prev`/`-dots`/`-next` keep
  positioning against `.messageboard` (the nearest positioned ancestor)
  as if it weren't there. Below 72rem it becomes a real flex row so the
  arrows flank the dots as a unit.
- **`.messageboard-expand { display: none }` must stay unscoped.** The
  mobile rule only styles it and `.is-visible` shows it; when the
  `display: none` lived only inside the media query, desktop got the
  browser's default `<button>` rendering (a plain gray bar).
  `messageboard.js` adds `.is-visible` only on mobile and only once the
  body is actually clamped.
- **Progress ring** (`.messageboard-dot.seen/active::before`): a
  `conic-gradient` driven by `--progress`, masked to a ring. The literal
  `black` in the `mask`/`-webkit-mask` gradients is alpha-only mask data,
  not a theme color — don't swap it for a color token.

## Mobile card: line clamp instead of internal scroll

Below 72rem `.messageboard-body` drops its internal scroll for a 6-line
`-webkit-line-clamp` (needs the `display: -webkit-box` +
`-webkit-box-orient: vertical` + `overflow: hidden` combo alongside it),
and the drag scrollbar is hidden. Dragging inside a small scroll box
fought the page's own scroll/rubber-band on touch; "View full message"
(`.messageboard-expand`) opens the full text in the modal instead.

## The "View full message" modal (`messageboard_modal.css`)

Same pattern as `tool_page.html`'s `.tool-lightbox`.
`position: fixed; inset: 0` and the backdrop come from
`06_components/shared/modal_base.css`; this file adds z-index, flex
centering and `:not([hidden])` display. Not media-query-gated: only ever
opened from `.messageboard-expand`, which is only shown on mobile.

- **`dvh` with a `vh` fallback**: `.messageboard-modal-panel` and
  `.messageboard-modal-scroll` declare `max-height` twice, `vh` first then
  `dvh`, so `dvh` wins where supported. `vh` is pinned to the viewport
  size from before the mobile address bar shows/hides, so the available
  height drifted out of sync — which made `messageboard.js`'s "hide the
  fade near the bottom" check look right when it ran, then wrong once the
  browser chrome settled. Keep the order (`vh` then `dvh`).
- **Non-scrolling shell**: only `.messageboard-modal-scroll` scrolls; the
  panel's `0.35rem` padding is a gutter so the scroll area's scrollbar
  lands inside the border/corner. The scroll area's `calc(… - 0.7rem)`
  subtracts that padding twice.
- **`overscroll-behavior-y: contain`** on `.messageboard-modal-scroll`:
  without it, dragging past the edges chains into the page underneath and
  can trigger pull-to-refresh.
- The scroll area's top padding (`2.5rem`) clears the floating close
  button. The close button has a filled circle background (like
  `.tool-lightbox-close`) because a bare "x" blended into the panel.
- **`.messageboard-modal-fade`** is a sibling of the scroll area, not a
  child, so it stays pinned to the panel's bottom edge regardless of
  scroll position; `messageboard.js` toggles `.is-visible` and re-checks
  on scroll. It uses `bottom/left/right: 0`, not the panel's padding
  inset — absolute offsets already resolve against the panel's padding
  box, so insetting again left a visible gap.
- **`.messageboard-modal-signature { padding-bottom: 4.5rem }`** equals
  the fade's `height: 4.5rem` on purpose: a belt-and-suspenders buffer so
  that even if the fade is still visible at max scroll (JS timing against
  browser-chrome resizing needed several attempts to get right), it only
  ever covers blank space, never the signature. Change both together.
