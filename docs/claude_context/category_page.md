# CategoryPage / ArticleIndexPage CSS — design rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/category_layout.css, ifiplatform/apps/ifi_home_app/static/css/06_components/category/category_header.css

Covers `ifi_home_app/static/css/05_objects/category_layout.css` and
`06_components/category/category_header.css`. (The banner is in
`title_banner.md`; cards in `cards.md`.)

`category_layout.css` holds only layout/positioning: the card grids
(`.category-grid`, and centering for `.newsbar-layout`/`.tool-grid`/
`.union-grid` on these pages) and the union-group row. Page identity
(typography, section headings, the accent h1 underline) lives in
06_components: `category_header.css`, `shared/section_heading.css`,
`shared/page_title.css`.

## category_layout.css

- `.category-page, .article-index-page { text-align: center }`: both page
  types share the same template shape (title, intro, general info, card
  grids) and are centered, unlike `ArticlePage`'s left-aligned prose
  (`article_layout.css`). `StudentUnionCategoryPage` uses the plain
  `.category-page` wrapper too (`studentunion_category_page.html`).
- `.union-group-row` / `.union-group-row-item`: a "row" block of
  `StudentUnionCategoryPage.union_groups` (`union_group.html`) — several
  titled groups side by side. `flex-wrap: wrap` plus `flex: 1 1 18rem;
  min-width: 0` on the items is what makes it wrap to stacked on a narrow
  viewport instead of squeezing every group; the small `min-width` is what
  triggers the wrap ("flex-basis big, min-width small", same combo as
  `.newsbar-layout`).
- `.union-group-row .section-heading { margin-top: 0 }`: each item's heading
  would otherwise add its own top margin on top of the row's gap.

## category_header.css

- `.category-page h1, .article-index-page h1 { font-size: 2.75rem }`:
  landing-page-sized title, larger than the default ~2rem the shared
  `.category-page h1` rule in `shared/page_title.css` leaves it at.
  `ArticlePage`'s h1 is sized by `ArticleStyle.title_font_size` instead and
  isn't touched here.
- `#page-title-plain[hidden] { display: none }` is required.
  `#page-title-plain` (`page_title_banner.html`, toggled by
  `banner_style.js` when the banner is shown) would otherwise stay visible:
  `.category-page h1 { display: inline-block }` in `page_title.css` is
  author CSS, which beats the UA stylesheet's `[hidden] { display: none }`.
  The id selector guarantees this rule wins over any h1 rule. Same issue as
  `.title-banner[hidden]` and `.quick-style-field[hidden]` in
  `article_quick_style.css`.
- `.intro` (lead paragraph, 1.15rem) and `.general-info` (smaller, muted
  secondary note) — see `CategoryPage.general_info`/
  `ArticleIndexPage.general_info` help_text.
- `.intro p` / `.general-info p { font-size: inherit }` is required: both
  render via `|richtext` as `<p>`, and the global `p { font-size: 1.05rem }`
  in `elements.css` is set on the tag directly, which always beats
  inheriting the parent's size regardless of specificity. Same fix as
  `.article-header > .intro p` (`article_header.css`) and `.union-core p`
  (`union_core.css`).
