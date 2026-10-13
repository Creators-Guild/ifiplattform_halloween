# Article body block CSS — design notes

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/article/article_alignment.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article/article_image.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article/article_multicolumn.css

Covers `ifi_home_app/static/css/06_components/article/article_alignment.css`,
`article_image.css` and `article_multicolumn.css`.

## Common pattern: editor values are inline, mobile resets need `!important`

Block font-size, side/box padding, image width (`width_rem`), column gap
and column weights (`flex-basis`) are free-form rem numbers from
`ArticleBlockStyle`, written as inline styles (`article_body_blocks.html`,
`article_column_content.html`, `article_image_block.html`,
`_block_box_style.html`), with no min/max clamp. Inline styles beat any
stylesheet rule, so every `@media (max-width: 45rem)` reset in these files
uses `!important`. Resets only touch sizing (font-size, padding,
flex-basis) — box background/border/radius and text color stay. Breakpoint
is 45rem (not the old 480px/640px) for the reason in `article_layout.md`;
the 640px multi-column version shipped a real bug (an editor's 15.25rem
side padding plus 5rem gap blew the row past the screen on phones between
640 and 720px wide).

## article_alignment.css

- Two class families, `.prose--align-*` (paragraph) and `.heading--align-*`
  (h2–h5 headings *and* `h3.column-title`). Headings can't reuse the
  `.prose` stem: plain `.prose` is also the sitewide "rendered richtext"
  marker class.
- `.prose p { font-size: inherit }`: the paragraph's RichTextBlock renders a
  `<p>`, and the global `p { font-size: 1.05rem }` (`elements.css`) sets
  size directly on the element, which beats inheritance from `.prose`
  (including the mobile `!important` reset) no matter the specificity.
  Same fix as `.article-header > .intro p`.
- Mobile reset sizes: headings/column titles go to `1.5rem`, not 1rem, so a
  heading still reads as a heading; paragraphs go to `1rem`.

## article_image.css

- `figcaption { width: 0; min-width: 100% }`: left/right figures are
  floated with `width:auto` (shrink-to-fit). Without `width:0` a long
  caption's max-content width stretches the whole figure (and the 100%-wide
  image). `min-width:100%` then fills whatever width the image produced.
  `overflow-wrap: anywhere` is still needed for unbreakable strings (long
  URLs) that would otherwise overflow the box.
- Image width is inline `width` (not `max-width`), plus an inline
  `max-width:100%` safety net: a floated shrink-to-fit figure falls back to
  the image's intrinsic size, so `max-width` alone could only shrink an
  image, never enlarge it.
- Mobile padding reset: `.hero-image-figure` only resets
  `padding-left/right` (editor `hero_image_side_padding`), not the
  shorthand, because `.image-figure--boxed`'s fixed `padding: 1rem` is meant
  to stay. `.body-image-figure` has no fixed padding class, so it resets
  the whole `padding`.
- `.image-figure--boxed`: border-radius and box-shadow come inline
  (`box_border_radius`, `hero_image_box_shadow_*`), not from this rule.

## article_multicolumn.css

- `.multi-col-grid { clear: both }` plus `.multi-col-grid +
  .body-image-figure { clear: both }`: floats never sit beside a
  multi-column block in either direction.
- `.multi-col-item .body-image--left/--right { float: none }`: floated
  images inside a narrow flex column spill out next to it instead of
  wrapping text, so images in columns always stack, at every screen size.
  Width/max-width are deliberately not touched here — they're inline.
- Mobile: columns stack (`flex-direction: column`), `flex-basis: auto
  !important` overrides the inline column weights, and grid/item padding is
  reset.
