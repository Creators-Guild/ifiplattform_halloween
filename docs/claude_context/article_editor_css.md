# Article editor-mode CSS — design notes

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/06_components/article_editor/article_block_panel.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_editor/article_block_trigger.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_editor/article_color_picker.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_editor/article_quick_style.css, ifiplatform/apps/ifi_home_app/static/css/06_components/article_editor/article_unsaved_changes.css

Covers `ifi_home_app/static/css/06_components/article_editor/`:
`article_block_panel.css`, `article_block_trigger.css`,
`article_color_picker.css`, `article_quick_style.css`,
`article_unsaved_changes.css`.

## Shared base files

Several selectors here look incomplete because part of their styling lives
in shared files — don't re-add it locally:
- `../shared/popover_base.css`: background-color/border of
  `.quick-style-panel` and `.block-style-mini-panel`; full header-row layout
  of `.quick-style-panel-header`/`.block-style-mini-panel-header`;
  margin/font-weight of the `*-title` classes; flex/cursor of
  `.block-style-close`/`.quick-style-minimize`.
- `../shared/modal_base.css`: `position: fixed; inset: 0` of
  `.unsaved-changes-modal` and the background of `.unsaved-changes-backdrop`.

## `[hidden] { display: none }` rules

`.block-style-field[hidden]`, `.block-style-box-fields[hidden]`,
`.quick-style-field[hidden]`, `.save-bar[hidden]`, etc. are required: the
class rule's `display: flex` beats the UA stylesheet's `[hidden] { display:
none }`, so JS toggling `hidden` would otherwise do nothing.

## z-index stack (all `position: fixed`)

quick-style panel `2000` < save bar `2001` < block-style mini panel `2010`
< unsaved-changes modal `3000`. The save bar must never hide behind the
quick-style panel; the mini panel and the modal take priority when open
(the modal can appear while a mini panel is open). `.editor-mode-toggle`
is `40`.

## Editor mode gating

`editor_mode_toggle.js` adds `body.editor-mode-on`; the quick-style panel,
block outlines and block triggers all key off that class.

## article_quick_style.css

- `.editor-mode-toggle` is `position: sticky` (not fixed) so it starts in
  flow at the top of `.article-page` (never overlapping the site header,
  which is outside `.article-page`) and pins at `top: 1rem`.
  `margin-left: auto` + `width: fit-content` keeps it right-aligned even
  when stuck. It's always visible to users with `can_edit_style` — it's the
  one control that turns editing back on.
- `.quick-style-panel` is fixed **bottom-left** because Wagtail's userbar
  sits bottom-right. `.is-minimized` (set by `article_quick_style.js`) hides
  `.quick-style-panel-body`, leaving just the header row.
- `.quick-style-field-hint` is separate from `.quick-style-status` because
  the status element is id-targeted by JS for live Saving/Saved/error text.
- `.article-draft-banner` is intentionally loud; it renders only when the
  page isn't live (`page_is_live` in `article_page.html`), which only
  editors can see (`ArticlePage.route()`).
- Mobile: the quick-style panel spans the full bottom edge.

## article_unsaved_changes.css

- `.save-bar` is a fixed bottom-center pill, available whenever there are
  unsaved changes; the modal only appears on navigation away.
- Mobile: `.save-bar { bottom: 6rem }` lifts it above the full-width
  quick-style panel instead of overlapping it.

## article_block_panel.css

- `.block-style-mini-panel` is `position: fixed` with top/left recomputed
  on every scroll/resize by `positionPanel()` in `article_block_style.js`,
  so it tracks its trigger icon.
- `max-height: calc(100vh - 1rem); overflow-y: auto` is required:
  `positionPanel()` only moves the panel back on-screen, never shrinks it,
  so with many sections expanded the Save/Reset row becomes unreachable.
- The Box/caption section collapse is a plain `[hidden]` toggle on
  `#block-style-box-fields` by JS, independent of whether the box is
  enabled; `.block-style-box-collapse-toggle[aria-expanded="false"]` rotates
  the chevron.

## article_block_trigger.css

- `.block-style-trigger` hides with `visibility: hidden; opacity: 0`, not
  `display: none`, so JS can still find and measure it.
- `.hero-image-figure.editable-block, .body-image-figure.editable-block {
  z-index: 5 }`: a later full-width block wrapping around a floated image
  still covers the image's area for hit-testing, and since both are
  `position: relative` with no z-index, DOM order made the later block
  swallow clicks on the image's trigger.
- Block highlight uses `outline` (not border) so nothing shifts in layout.
  `.is-editing` (on the block) and `.is-open` (on the trigger) are set by
  `article_block_style.js` to keep the highlight/trigger visible while the
  mouse is over the mini panel.

## article_color_picker.css

- `.color-swatch--custom` is a hex text input; `article_block_style.js`
  sets its background (and a readable text color) to the typed value. It
  needs an explicit `width: 7rem`: a text input's `width: auto` falls back
  to the browser's ~20-character intrinsic width and overflows the panel.
- `.color-swatch-picker` is a `<label>` with a conic-gradient background
  instead of styling the color input's vendor pseudo-elements, which
  rendered inconsistently across engines. Clicking the label opens the
  native picker of `.color-swatch-picker-input`, which is visually hidden
  (clip pattern), so no click-forwarding JS is needed.
- `.color-swatch-custom-group` groups the hex input and picker so they
  can't wrap onto different lines; `margin: 0 auto` centers it on its own
  wrapped line.
- Active ring for the custom color lives on the group:
  `.color-swatch--custom.active` undoes the generic `.color-swatch.active`
  ring (so it must stay after it), and
  `.color-swatch-custom-group:has(.color-swatch--custom.active)` applies it
  to the group — no extra JS.
