# newsbar_layout.css / newsbar_heading.css — design rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/newsbar_layout.css, ifiplatform/apps/ifi_home_app/static/css/06_components/newsbar/newsbar_heading.css

Covers `ifi_home_app/static/css/05_objects/newsbar_layout.css` —
the auto-fit card grid shared by the homepage's "Suggested News"/
"Suggested Info Articles" sections and the article index/category pages'
"Suggested Articles" section — and
`06_components/newsbar/newsbar_heading.css` (those sections' headings).

## Heading truncation: ellipsis, not wrap, not shrink-to-fit

`.newsbar-heading--news`/`--articles` reserve room for exactly one line
(`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`).
Reserving two lines up front left a permanent gap under whichever heading
only ever needed one, which was most of the time — this way the common
case (fits on one line) costs no extra space, and a too-long heading
truncates instead of wrapping and pushing the card grid down. A
JS-driven shrink-to-fit (scaling the font down instead of truncating) was
tried here and dropped — it looked jarring in practice, not worth the
added complexity. Only these two are centered; `.newsbar-heading--events`
(the homepage events box heading) is not.

## Full/short heading label: the `@container` query is currently inert

`home_index.html`'s articles heading holds both `.newsbar-heading-full`
("Suggested Info Articles") and `.newsbar-heading-short` ("Info
Articles"); `newsbar_heading.css` hides the short one by default and
swaps them under `@container (max-width: 26rem)`, meant to key off
`.articlesbar_container`'s own width rather than the viewport. **No
element currently sets `container-type`** (it used to be on
`.articlesbar_container` in `home_layout.css` before the grid rewrite), so
the container query never matches and the full label always shows,
relying on the ellipsis. The `26rem` threshold was also chosen against an
old fixed card-width cap that no longer exists (the grid now uses `1fr`,
below). Restoring `container-type: inline-size` on
`.articlesbar_container` would re-enable it; re-check the threshold if so.

## Why `grid-template-columns` uses `1fr`, not a fixed max card width

A *fixed* max (tried at both `26rem` and `30rem` before landing here) can
never fully avoid dead space: `auto-fit` only adds another column once
the container is wide enough for one more card at that max width, so at
any container width just *below* that threshold, whatever number of
cards already fit are stuck at their max size with the remaining leftover
width sitting empty beside them. Raising or lowering the max just moves
where that gap falls; it can't remove it.

`1fr` instead of a fixed `rem` removes it structurally: `auto-fit` still
decides *how many* columns fit using the minimum (`18rem`; `16rem` under
`45rem`) as usual, but every column that does fit then stretches to
evenly fill 100% of the container's width. The remaining trade-off — a
lone card in a very wide column growing quite large — is handled
separately: `.newsbar-layout .articlecard` caps the *card's* own
`max-width` (`40rem`, generously high so it only kicks in for extreme
cases) and `justify-self: center` re-centers it within its track, instead
of capping the track itself the way the rejected fixed-max approach did.
`justify-content: center` on `.newsbar-layout` centers the tracks as a
group (auto-fit's default `start` leaves leftover tracks flush-left).

## Why `align-items: start`, not grid's default `stretch`

Grid's own default (`align-items: stretch`) forces every card in a row to
match the tallest one, so a card with a short title/intro next to one
with a long, wrapping title/intro got stretched taller than its own
content needs. `start` lets each card size to its own content instead.

## `.newsbar-layout .articlecard`'s sizing: `height`/`aspect-ratio`/`width`

All load-bearing, not decorative:

- **`height: auto`**: `.articlecard`'s own `height: 100%` (`article_card.css`)
  is for its *other* use inside an editor-set explicit-height body block —
  within this grid the row's resolved height counts as definite, so
  `100%` would still stretch the card to match it.
- **`aspect-ratio: 5 / 4`**: locks the *whole card's* shape (image + title
  + meta + intro together), so News and Info Articles cards render
  identically sized/shaped as long as their tracks are the same width,
  regardless of how titles wrap. `.newsbar-layout .articlecard img`
  overrides the image's own `8/5` (`article_card.css`) to a shorter
  `2 / 1`, which frees enough vertical room inside the 5/4 box for the
  intro's 2-line clamp (`.articlecard-intro`, `line-clamp: 2`) instead of
  `overflow: hidden` (`article_card.css`) cutting it down to one line.
- **`min-height: 0`**: grid items get an "automatic minimum size" by
  default that lets them grow past their `aspect-ratio`-computed height to
  fit content — exactly what made some cards taller than others despite
  the locked ratio. `0` makes `aspect-ratio` authoritative and
  `overflow: hidden` clips instead.
- **`width: 100%`**: `justify-self: center` switches this item from
  grid's default stretch sizing to shrink-to-fit sizing, which computes
  the width from its *content's* intrinsic size — and percentage widths on
  descendants (`.articlecard img`'s `width: 100%`, the image crop via
  `aspect-ratio` + `object-fit`) can't resolve during that, so they fall
  back to intrinsic size. An unusually large source image (e.g. a tall
  logo/crest) could then pull the card wider than its track — overflowing
  the viewport on mobile, overlapping siblings on desktop — and its crop
  never applies. `width: 100%` keeps the sizing definite so `max-width`
  does the capping.

## `.articlecard--list` inside the grid

`.articlecard--list` (compact one-row variant) resets the card rules
above: `aspect-ratio: unset` (forcing 5/4 on its short content would leave
a big blank gap), `max-width: unset` + `justify-self: stretch` (it's meant
to span the row edge-to-edge, and the lone-card cap/centering would
shrink it to a narrow centered strip).

Under `45rem` it also gets `grid-column: 1 / -1` — `.articlecard--list`
alone doesn't know it's in a grid, so without it the item would keep a
card-sized track instead of spanning the row. The class is added by
`article_list_toggle.js` (default: every card past the first two; also
toggleable per card via `article_card.css`'s `.articlecard-toggle`) or by
the editor's "Show as list item" toggle (`article_block_style.js`) — one
shared look rather than a second set of rules. The `45rem` must match
`article_list_toggle.js`'s own `matchMedia("(max-width: 45rem)")`.

## Mobile (`max-width: 45rem`): dropping the `aspect-ratio` lock

Under `45rem`, `.newsbar-layout .articlecard` drops the `5/4` lock back to
content-driven height (`aspect-ratio: unset; height: auto`). An expanded
(non-`--list`) card's image + h3 + meta + intro no longer fit inside the
shrinking, width-derived box, and `overflow: hidden` was clipping the
intro rather than the card growing. At this width the grid is effectively
single-column anyway, so there's rarely a row-mate to match.
(`max-width: 40rem`/`justify-self: center` don't need resetting — the
base rule's `width: 100%` keeps them a no-op at any track narrower than
`40rem`.)
