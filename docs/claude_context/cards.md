# Card CSS — shared patterns + category/tool cards

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/cards/category_card.css, ifiplatform/apps/ifi_home_app/static/css/06_components/cards/tool_card.css

Covers `ifi_home_app/static/css/06_components/cards/category_card.css` and
`tool_card.css`, plus the patterns all four card files share
(`article_card.css` and `union_card.css` have their own notes,
`article_card.md`/`union_card.md`, for their card-specific details).

## `height: 100%` on the card itself (`.articlecard`, `.category-card`, `.tool-card`, `.union-card`)

Looks like a no-op, and it is — until the wrapping `.body-*-card` div
(`article_body_blocks.html`) gets an explicit height from the editor's
"Height" setting. Percentage height against an auto-height parent resolves
to auto, so it only takes effect then. It relies on
`box-sizing: border-box` and `overflow: hidden` from
`shared/card_base.css`: border-box so 100% includes the card's own
padding/border instead of overflowing the parent by that amount, and
overflow:hidden so content taller than the explicit height is clipped
cleanly. Don't remove it as redundant.

## `.body-*-card` width via `--card-width`, not an inline `width`

`.body-article-card`, `.body-category-card`, `.body-tool-card`,
`.body-union-card` all do `width: var(--card-width); max-width: 100%`. The
editor picks a free-form rem width (`width_rem`); the templates
(`article_body_blocks.html`/`article_column_content.html`) pass it as the
`--card-width` custom property rather than a literal inline `width` so the
`@media (max-width: 45rem)` override (`width: 100%`) can win at normal
specificity. An inline `width` would need `!important` to beat. It's
`width`, not just `max-width`, because a standalone card isn't a flex item:
`.category-card`'s `flex: 0 1 14rem` / `.tool-card`'s `flex: 0 1 18rem` /
`.union-card`'s `flex: 0 1 14rem` only apply inside `.category-grid` /
`.tool-grid` / `.union-grid`, and `.articlecard`'s `display: block` would
otherwise stretch to the full prose column.

`.body-*-card--fixed-height` (`height: var(--card-height); overflow: hidden`)
is added by `article_block_style.js` together with `--card-height` only when
the editor sets a nonzero `height_rem`; 0/blank leaves natural height.

## Mobile (`@media (max-width: 45rem)`)

Editor-chosen width/height are desktop-only: `.body-*-card` goes to
`width: 100%; height: auto`. `overflow: visible` (not hidden) there on
purpose — height is auto so nothing needs clipping, and `hidden` would clip
the card's hover-lift/shadow, which paints slightly outside its border box.

Each card also switches to a compact horizontal row at this width,
regardless of context (standalone in an article body or inside its listing
grid), because the stacked desktop tile wastes vertical space on a phone:
`.category-card` goes left-aligned with less padding; `.tool-card` puts a
4rem square image beside the title (and hides `.tool-card-link-hint`).

## `overflow-wrap: break-word` on card titles

`.category-card h2`, `.tool-card-body h3` (and `.union-card h3`): a long
single word with no spaces would otherwise overflow and get raw-clipped by
the card's `overflow: hidden` from `card_base.css`.

## tool_card.css specifics

- The tool card leans on the `::before` gradient bar plus the two-layer
  `box-shadow` glow on hover to read as "featured" among plainer
  category/article cards, since tools carry little content.
- `.tool-card-image` uses `aspect-ratio: 16 / 9`, not a fixed height, so it
  scales with the card's width (a fixed 9rem height used to distort/
  over-crop at narrow `width_rem` values or the 100% mobile width).
- `.tool-card-category` shows the tool's direct parent category
  (`tool.get_parent.title`) — needed once `CategoryPage.show_nested_tools`
  (`article_models.py`) flattens tools from several subcategories into one
  grid.
