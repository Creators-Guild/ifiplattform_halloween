# article_card.css — design history

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/cards/article_card.css

Covers `ifi_home_app/static/css/06_components/cards/article_card.css`.
The `height: 100%`, `.body-article-card` `--card-width`/`--card-height`
and mobile `overflow: visible` patterns are shared with the other cards —
see `cards.md`.

## `.articlecard--list`: why plain block flow, not a flex row

The editor-picked `list_style` (`article_body_blocks.html`'s "Show as list
item" toggle, `ArticleBlockStyle.list_style`) collapses a card down to
title left, meta as a right-aligned block, image/intro dropped. The same
class is also applied/removed directly by `article_list_toggle.js` for
the homepage newsbar/articlesbar grids on narrow screens (see
`newsbar_layout.css` and `.articlecard-toggle`) — one shared look for both
"editor picked list style on purpose" and "visitor collapsed this card
themselves", rather than two separately maintained sets of rules for
what's visually identical.

The current layout is title on its own full-width row, date/author below
it in smaller, muted text. It used to be a side-by-side row instead
(title left, meta right-aligned), but the meta column ate enough width
that the title itself had barely any room left and truncated hard (e.g.
"News Artic..."). Plain block flow now (no longer its own flex column) —
the draft badge, h3, meta, and intro are already stacked in that order by
normal document flow, so an outer `display: flex` wasn't actually needed
for the layout itself, only for the row→column switch from the *old*
side-by-side look. Kept as block specifically so this card-wide toggle
animates smoothly on mobile (the `max-height`/`opacity`/`margin`
transitions on `img` and `.articlecard-intro`, and `padding` on
`.articlecard` itself) — switching `display` or `flex-direction` can't be
transitioned by CSS at all, it just snaps instantly, which is what this
avoided.

## The `max-height` caps on `.articlecard img` (30rem) and `.articlecard-intro` (3rem)

Both look pointless while expanded — the image is never 30rem tall, and
the intro is already line-clamped to 2 lines. They exist so the
`.articlecard--list` collapse (`max-height: 0; opacity: 0`) has a real
starting value to transition from. Don't replace the collapse with
`display: none`; it can't animate.

## `.articlecard-meta > span + span::before`

The "|" separator between author and date spans (`article_card.html`).
Adjacent-sibling so it only appears when both spans exist — no dangling
separator. Its `margin-right: 0.75rem` mirrors the flex row's column-gap
(the `0.75rem` in `.articlecard-meta`'s `gap: 0.25rem 0.75rem`) so the
"|" sits centered between the two words; change both together.

## `.articlecard-draft-badge`

Editor-only (see `article_card.html`). Uses `--color-error`, the same red
as `.quick-style-status-badge--draft` in `article_quick_style.css`, so a
draft reads the same everywhere.

## `.articlecard--unlocked-ratio img`

Editor-picked `fixed_ratio=False` (`ArticleBlockStyle.fixed_ratio`, "Lock
image ratio" toggle). Normally `aspect-ratio: 8 / 5` scales the image with
the card width, so an explicit card height has nothing to fill. Unlocking
drops the ratio for a fixed `height: 10rem`, so a card height actually has
visible effect; `object-fit: cover` on `.articlecard img` still crops it.

## `.articlecard-toggle` (expand/collapse button)

Driven by `article_list_toggle.js`. `display: none` everywhere except the
final `@media (max-width: 45rem) { .newsbar-layout .articlecard-toggle }`
rule — only homepage newsbar/articlesbar grids on narrow screens show it.
It's nested inside the card's `<a>` (`article_card.html`), so it's
absolutely positioned (anchored by `position: relative` on `.articlecard`)
with `z-index: 1` above the card's click target, and the JS click handler
stops navigation.

The translucent `color-mix(... var(--color-ink) 55%, transparent)`
background (no border) is deliberate: the button is mostly seen on top of
the card photo (it shows while expanded), and a light bordered chip read as
a stark badge there.

The chevron is an inline SVG (`article_card.html`), not a CSS
border-triangle — a border-triangle only paints half its box, so it
couldn't be centered or rotated without hand-tuned per-state offsets. The
SVG centers via the button's flexbox and rotates around its real middle.
`.articlecard-toggle svg`'s `width: 1.3rem; height: 0.73rem` matches the
viewBox's 16:9 ratio so the shape fills the box; keep that ratio if
resizing. Default `rotate(180deg)` points down ("expand");
`[aria-expanded="true"]` rotates back to up. `article_list_toggle.js`
toggles `.articlecard--list` and `aria-expanded` together.
