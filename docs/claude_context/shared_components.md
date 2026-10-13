# Shared CSS components (06_components/shared/)

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/shared/block_box.css, ifiplatform/apps/ifi_home_app/static/css/06_components/shared/card_base.css, ifiplatform/apps/ifi_home_app/static/css/06_components/shared/modal_base.css, ifiplatform/apps/ifi_home_app/static/css/06_components/shared/page_title.css, ifiplatform/apps/ifi_home_app/static/css/06_components/shared/popover_base.css, ifiplatform/apps/ifi_home_app/static/css/06_components/tool/tool_lightbox.css

Files under `ifiplatform/apps/ifi_home_app/static/css/06_components/shared/`.
The three `*_base.css` files group selectors from several components and
hold only the declarations that are identical for all of them. Anything that
differs stays in each component's own file. Don't move a look-alike property
into a base file without checking every selector in the group.

## card_base.css

- Groups `.articlecard` (`cards/article_card.css`), `.category-card`
  (`cards/category_card.css`), `.tool-card` (`cards/tool_card.css`) and
  `.union-card` (`cards/union_card.css`).
- Border, `border-radius`, `box-shadow` and `color` stay per-card because
  they differ: `.articlecard` has a 3px radius, `.tool-card` 14px, the other
  two 12px, and `.tool-card`'s `box-shadow` has an extra glow layer.
- `position: relative` is deliberately left out. `.union-card` has no
  absolutely-positioned children and doesn't set it. Adding it here would
  give `.union-card` a new positioning/stacking context.

## modal_base.css

- Groups `.unsaved-changes-modal` (`article_editor/article_unsaved_changes.css`),
  `.toc-modal` (`article_toc/article_toc_modal.css`), `.tool-lightbox`
  (`tool/tool_lightbox.css`), `.messageboard-modal`
  (`home/messageboard_modal.css`) and `.event-calendar-modal`
  (`event/event_calendar.css`). Only `position: fixed; inset: 0` is shared.
- `z-index` is not shared. `.unsaved-changes-modal` uses 3000 because it
  can open while an editor panel (z-index 2000/2010) is already open. The
  other four use 1000.
- `display` is not shared. Two different patterns are in use:
  `.unsaved-changes-modal`, `.toc-modal` and `.tool-lightbox` default to
  `display: flex` and hide with a `[hidden]` rule, while
  `.messageboard-modal` and `.event-calendar-modal` default to
  `display: none` and show with `:not([hidden])`.
- The translucent `color-mix(...)` backdrop goes on the modal shell for
  `.tool-lightbox`, `.messageboard-modal` and `.event-calendar-modal`. For
  the other two it goes on a separate backdrop child instead
  (`.unsaved-changes-backdrop`, `.toc-modal-backdrop`). Don't also add it
  to `.unsaved-changes-modal` or `.toc-modal`: the two layers would stack
  and make the backdrop darker.
- The `body.*-open { overflow: hidden }` scroll-lock group has no
  `.unsaved-changes-modal` entry on purpose. It's a short confirm dialog
  that never needed to block page scroll.

## popover_base.css

- Groups `.toc-overlay-panel` (`article_toc/article_toc_overlay.css`),
  `.block-style-mini-panel` (`article_editor/article_block_panel.css`),
  `.quick-style-panel` (`article_editor/article_quick_style.css`) and
  `.position-info-panel` (`union/union_position_info.css`), plus their
  `-header`, `-title` and close/minimize button selectors.
- These stay per-file: `position` (two panels are absolute, two are fixed),
  `border-radius` (10px on `.block-style-mini-panel`, 12px on the others),
  `box-shadow` (`--color-shadow-strong` on the two fixed panels,
  `--color-shadow` on the others), the header's bottom margin, the title's
  font-size and color, and the close button's look (a bordered text chip on
  toc-overlay/position-info, a round icon button on block-style/quick-style).

## block_box.css

- `.block-box` is the on-page editor's replacement for the old Wagtail
  "box" block. The background, border and radius come from inline styles
  written by `_block_box_style.html`, so this file only sets `box-sizing`.
- The class goes directly on the boxed element (a heading, `.prose`, a body
  image figure, a multi-column grid or one of its items), not on a wrapper.
  `box-sizing: border-box` keeps the border and padding from adding to that
  element's own width (such as an image's `width_rem`) or breaking a
  column's flex sizing.
- `overflow-wrap: break-word` stops a long unbroken word or URL from
  pushing the box wider than its container.

## page_title.css

- `--title-font-size` is set on `.article-header` in `article_page.html`
  from `ArticleStyle.title_font_size`. The `2rem` fallback in
  `.article-page h1` is the browser's default h1 size, so pages without an
  override look the same as before.
- The value is multiplied by `--content-font-size-multiplier`, which is set
  on `.article-page` (the Global editor's font-size multiplier). `.intro` and
  `.article-meta` in `article_header.css` scale the same way.
