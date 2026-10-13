# article_header.css — design notes

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/article/article_header.css

Covers `ifi_home_app/static/css/06_components/article/article_header.css`.
Title/meta/intro are wrapped together in `.article-header`
(`article_page.html`) so they share one hover trigger/mini panel, but each
keeps its own alignment/font-size.

## Why title/intro/meta each got their own alignment control

`.article-page`'s own `--content-alignment` (consumed via `text-align`)
used to also govern the title/intro/meta group — they inherited it rather
than having their own value. Editors wanted the title and intro alignable
separately from each other (and from the body), so each got its own
control (`ArticlePage.title_alignment`/`intro_alignment`/`meta_alignment`,
`--title-alignment`/`--intro-alignment`/`--meta-alignment`). `--content-alignment`
is now only a fallback for anything with no alignment control of its
own — rare, since most block types (heading/paragraph/image/multi_column)
set `text-align` explicitly on themselves, which always wins over this
inherited value regardless of specificity.

## Selector-level gotchas

- `.article-header { text-align: var(--title-alignment) }` is what
  positions the h1: `.article-page h1` is `display: inline-block`
  (`shared/page_title.css`), and an inline-block is positioned by its
  containing block's `text-align`, not its own. Putting it on h1 does nothing.
- `.article-header`'s `border-bottom` is a separator (same accent color as
  h1's underline, thinner). `.article-header.block-box { border-bottom:
  none }` exists because a boxed header (`header_style.box.enabled`) with
  no border of its own (just background/shadow) otherwise leaves this line
  poking out under the box. When the box *does* have a border, the inline
  `border:` shorthand from `_block_box_style.html` already overrides it.
- `.article-header > .intro p { font-size: inherit }`: `page.intro|richtext`
  renders a `<p>`, and the global `p { font-size: 1.05rem }` in
  `elements.css` sets size directly on the element, which beats inheritance
  from `.intro` regardless of specificity. Same fix as `.prose p` in
  `article_alignment.css`.
- `.article-header > .article-meta` uses `justify-content`, not
  `text-align`: `.article-meta` is a flex container, and flex items ignore
  inherited text-align. `left`/`center`/`right` are valid justify-content
  values, so the same `--meta-alignment` value works. Scoped under
  `.article-header >` because `.article-meta` (`article_meta.css`) is shared
  with union/tool pages that have no such override. Fallback font size
  `0.9rem` matches `article_meta.css`'s default.
- `.article-header > .translation-warning-row` follows `--meta-alignment`
  (it's meta content on its own line). text-align must be on this full-width
  wrapper, not on `.translation-warning` itself — a block box can't position
  itself with its own text-align.
- Intro/meta font sizes are `calc(var(--X-font-size) *
  var(--content-font-size-multiplier, 1))`: the Global editor's multiplier
  (set on `.article-page`) scales on top of the stored value, same as
  `_effective_heading_style()` does for body blocks.

## Mobile (`max-width: 45rem`)

- Title, intro, meta row and translation-warning row are all forced to
  **center** (not reset to left).
- `--title-font-size`/`--intro-font-size`/`--meta-font-size` are reset with
  `!important` on `.article-header`, and `--content-font-size-multiplier` is
  pinned to `1 !important` — otherwise the reset sizes would still be
  scaled by the Global multiplier via the `calc()`s above. `!important` is
  needed because these custom properties are set inline.
- `.article-page h1`, `.intro`, `.article-meta` get `padding: 0 !important`
  to kill their inline box padding (`_effective_box_style()`,
  `box.padding`). Box background/border/radius are deliberately left alone —
  only sizing that can overflow is reset.

### Why the breakpoint is 45rem, not 480px

This reset used to fire at `480px` — narrower than `45rem` (720px), the
breakpoint every other mobile treatment on the site uses (see
`article_layout.md`). A visitor in the 480px–45rem gap got none of it:
editor-picked padding/alignment/font-size stayed at desktop values on a
phone. Moved to `45rem` to close that gap.
