# Article table of contents CSS — design notes

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/article_toc/article_toc_modal.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_toc/article_toc_overlay.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_toc/article_toc_trigger.css

Covers `ifi_home_app/static/css/06_components/article_toc/`:
`article_toc_trigger.css`, `article_toc_overlay.css`,
`article_toc_modal.css`. Behaviour is in `table_of_content.js`.

## Desktop: gutter icon + anchored popover

- `.article-page--has-toc` reserves a left gutter out of `.article-page`'s
  own padding; `.toc-open-sticky` is pulled into it with an equal negative
  margin, so the icon can't overlap the sidebar or the article text
  regardless of the collapsible sidemenu's width. Both sizes derive from
  `--toc-icon-size` (`ArticlePage.toc_icon_size`, set inline on
  `.article-page`), as does `.toc-open-button` (icon + fixed 1.45rem ring) —
  change them together.
- `.toc-open-sticky` is `position: sticky; height: 0` (not fixed) so it
  tracks the article column horizontally and keeps sticking down the whole
  tall `.article-page`.
- `.toc-open-sticky + * { margin-top: 0 }`: being before the first content
  block stops that block's top margin from collapsing through `.article`,
  which would otherwise double the gap under `.article-meta`.
- `.toc-overlay-panel` is `position: absolute` relative to
  `.toc-open-sticky` (sticky establishes a containing block just like
  relative). No backdrop — the page stays interactive; JS closes it on
  outside click, Escape, or choosing a link. Background/border and the
  header/title/close base styles come from `../shared/popover_base.css`.

## Mobile (`max-width: 45rem`): title button + full-screen modal

- The gutter icon is hidden and `.toc-title-sticky` (first child of
  `.article-page`, before `.article-header`) shows `.toc-title-button`,
  which opens `.toc-modal` — a centered dialog with backdrop, since there's
  no room for an anchored popover. `position: fixed; inset: 0` and the
  backdrop color come from `../shared/modal_base.css`.
- `.toc-title-sticky { margin-top: 1rem }` mirrors h1's top margin so the
  button lines up beside the title instead of above it.
- `.toc-title-button` is `position: absolute`, not float — a float would
  reflow/rewrap the h1 around it; overlapping the title is intended.
- Below 45rem the floating `.toc-open-sticky` button is hidden and
  `.article-page--has-toc` drops its left padding; `.toc-title-sticky` next
  to the h1 takes over. (A former 640px tier that shrank the floating
  button was removed once both breakpoints became 45rem — it was fully
  overridden.)
