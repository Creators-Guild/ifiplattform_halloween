# ifi_home_app CSS structure

The sitewide CSS architecture (ITCSS layers, how stylesheets are loaded,
BEM) is described in [docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md).
This file only covers what is specific to this app's CSS.

This tree starts at 05 because it only has objects and components.
`05_objects/` is a flat list (one layout file per area); `06_components/`
has subfolders grouping related files together. Lives directly under `css/`, not nested inside a `styles/neon_style/`
wrapper -- there's only ever one theme, so that extra nesting added path
length without adding organization.

```
05_objects/    -- one <area>_layout.css per area: article, category,
                  event, home, newsbar, tool, union
06_components/ -- styled pieces, one subfolder per area or widget family
                  (article/, article_editor/, article_toc/, cards/,
                  category/, event/, home/, newsbar/, tool/, union/), plus
                  shared/ for pieces used by more than one area, and
                  admin/ for the few Wagtail admin additions (loaded by
                  wagtail_hooks.py's insert_global_admin_css, not by the site)
```

An "area" is a Wagtail page type (ArticlePage, EventPage, UnionPage,
ToolPage, the category/index pages) or the home page (`home/`: events box,
message board, shortcuts, mobile navbar).

## Naming conventions

- **Layout files** live directly in `05_objects/` and are always named
  `<area>_layout.css` (`event_layout.css`, `union_layout.css`). They only
  place things: flex/grid, widths, gaps, alignment, breakpoints. No
  colours, borders, shadows or font styling.
- **Component files** live in `06_components/<area>/` and are named after
  the piece they style, not the page it appears on: `event_badges.css`,
  `event_list.css`, `union_header.css`, `tool_cta.css`.
- There are no `_page.css` files. The name came from the Wagtail page types
  (`event_page.css` was "all CSS for EventPage"), but the folder already
  says which page type a file belongs to, and a whole-page file mixes
  layout and components, which ITCSS keeps apart.
- A component used by several areas goes in `06_components/shared/`
  (`section_heading.css`, `page_title.css`).
- A large file mixing unrelated concerns is split by concern into several
  small files under one subfolder, rather than kept as one long file (e.g.
  `article_toc.css` -> `article_toc/article_toc_trigger.css` +
  `article_toc_modal.css` + `article_toc_overlay.css`).
- A reusable widget carved out of a larger file (e.g. the union page's
  member grid) gets its own component file -- `union/union_member_card.css` (the card grid) and
  `union/union_position_info.css` (its hover popover) are two separate
  components, not one file, since the popover is a distinct concern reused
  from the same `popover_base.css` pattern as `article_toc_overlay.css`.
- `06_components/shared/` holds two kinds of files: genuinely
  cross-component base files (`card_base.css`, `modal_base.css`,
  `popover_base.css`), and small standalone utilities used by more than
  one page/component (`block_box.css`, `article_meta.css`,
  `translation_warning.css`).

## Entry points (template partials, not CSS files)

Templates never link a leaf file from `05_objects/` or `06_components/`
directly. They include one partial per tier, and the partial holds the
`<link>` tags -- see [docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md)
for the block-per-tier mechanism and the three rules that come with it,
the first of which is **never use `@import`**.

The partials live in this app's template tree, not here beside the CSS:

```
apps/ifi_home_app/templates/css_links/
  home_base.html            -- app tier: what EVERY page here needs,
                               included once in home_base.html
  home_index.html           -- section tier: one per page family.
  article.html                 category.html covers both
  category.html                article_index_page and
  studentunion_category.html   article_category_page, whose
  union.html                   stylesheet needs are identical.
  event.html
  event_index.html
  tool.html
  article_editor.html       -- page tier: editor mode only, included
                               behind {% if can_edit_style %} so ordinary
                               visitors never download it
```

Ordering constraints live in those partials now, written once, instead of
being something every template has to get right:

- A shared base file (`card_base.css`/`modal_base.css`/`popover_base.css`)
  is linked *before* the specific component file(s) that use it, so the
  specific file can still override it. Never link a base file *after*
  those components -- it would win instead. This is why
  `popover_base.css`/`modal_base.css` sit in `category.html` and
  `studentunion_category.html` unconditionally, even though only editor
  mode uses them, rather than in `article_editor.html`.
- `title_banner.css` is linked after `category_header.css`,
  `section_heading.css` and `page_title.css`. Its `.title-banner h1` rule
  undoes the page title's underline and has the same specificity, so it
  only wins by coming later.
- `translation_warning.css` is linked last in every section partial:
  `06_components/article/article_header.css` also styles
  `.translation-warning`, and this one has to win.
- `home_eventsbox.css` (the events box's look) is linked in
  `home_index.html`, while its size and position stay in `home_layout.css`
  -- same `.eventsbox_container` selector, split into layout and look.
- In `home_base.html`, `06_components/sidemenu.css` comes after
  `home_layout.css` for the same reason -- both style `.sidemenu`.
