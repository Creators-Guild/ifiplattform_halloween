# title_banner.css — design rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/category/title_banner.css

Covers `ifi_home_app/static/css/06_components/category/title_banner.css`.

## What `.title-banner` is and where its config comes from

Optional decorative banner behind the title — `CategoryPage`/
`ArticleIndexPage`'s own `PageBannerStyle` (see `BannerStyleMixin` in
`article_models.py`), edited on-page via editor mode
(`banner_style_panel.html`/`banner_style.js`), not a Wagtail `FieldPanel`.
Flat color, not a gradient/image — `banner_color`/`--dot-color` and the
title's own color are all editor-chosen hex values (inline style, see
`article_category_page.html`/`article_index_page.html`), each with a
fixed fallback when left blank. Width/height default to `auto` (plain
full-width block, height driven by its own padding/content) —
`banner_width_rem`/`banner_height_rem` set an explicit inline width/height
instead when chosen (`0`/blank stays `auto`, see `PageBannerStyle`'s own
comment). `title_banner.js` scatters the actual dot pattern (a handful of
soft circles) into this at load.

## `.title-banner`

- `position: relative` + `overflow: hidden` position and clip the
  `.title-banner-circle` dots.
- `margin: 0 auto 1.5rem`: auto side margins keep an editor-constrained
  width centered. `text-align: center` on `.category-page`/
  `.article-index-page` only centers inline content, not a block's box.

## `.title-banner[hidden] { display: none }`

Required. `.title-banner`'s `display: flex` (needed to vertically center the
h1) ties with `[hidden]`, and author CSS beats the UA stylesheet's
`[hidden] { display: none }`, so without this rule the banner stays visible
while hidden. Same issue as `#page-title-plain[hidden]` in
`category_header.css` (see `category_page.md`).

## `.title-banner h1` — two rules, source order matters

The first rule sets `position: relative; z-index: 1` (above the dots) and
`overflow-wrap: break-word`: a long single-word title would otherwise
overflow and be clipped by the banner's `overflow: hidden` instead of
wrapping.

The second rule (`display: block; border-bottom: none; padding-bottom: 0`)
cancels the accent underline from `.category-page h1` in
`shared/page_title.css` (`display: inline-block; border-bottom: 4px ...`),
which would show as a stray line inside the banner. Both selectors are the
same specificity (0,1,1), so this only wins because `title_banner.css` is
linked after `page_title.css` in `templates/css_links/category.html` and
`studentunion_category.html`. Don't reorder those links or move this rule
earlier.

## `.title-banner-circle`

One dot; `title_banner.js` randomizes each circle's position and size, this
rule is only the shared part. Color comes from `--dot-color`
(`banner_dot_color`, set on `.title-banner`, independent of the banner
background) via inheritance, with a `#ffffff` fallback.
`mix-blend-mode: overlay` rather than a flat rgba tint is the fix for dots
disappearing or just darkening on some banner colors — overlay reads as a
soft highlight on any base color.
