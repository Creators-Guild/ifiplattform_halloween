# views/article_views.py — design notes

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/views/article_views.py

Context for future Claude sessions. Not a human-facing doc.

## BLOCK_STYLE_FIELDS

Per-block-type allow-list of which `ArticleBlockStyle` fields
`save_block_style` accepts — the server-side mirror of what each block
type's on-page mini panel actually offers.

- `"image_caption"`: an image's own title (`alt_text`)/caption, boxed
  together as one unit (its own `<figcaption>`), independent of the image's
  own box — keyed by synthesized `"<image-block-id>-caption"`.
- `"image_title"`/`"image_caption_body"`: the title/caption *text* itself
  (alignment/font-size/side-padding/color), independent of each other and
  of the figcaption's box — keyed by `"<image-block-id>-cap-title"`/
  `"-cap-body"`.
- `"column_title"`: a multi_column column's own title — alignment/
  font-size/text-color only (no box/side-padding of its own — edited from
  the same trigger/panel as its column, `FIELDS_BY_TYPE.column` in
  `article_block_style.js`, sent as a second independent save request
  alongside the column's own box fields), keyed by synthesized
  `"<column-uuid>-title"`.
- `"title"`/`"meta"`/`"intro"`: the article-header group, keyed by fixed
  pseudo ids `"article-title"`/`"article-meta"`/`"article-intro"`.
  Alignment/font-size live on dedicated `ArticlePage` fields instead, saved
  via `save_header_style` (`article_block_style.js`'s `recordPendingEdit`)
  — only side padding/box/text color/the "lock alignment" opt-out go
  through `ArticleBlockStyle` here, so `save_quick_style`'s global-alignment
  bulk-overwrite can respect `exclude_from_global_alignment` the same way
  it does for every other alignment-capable block type.
- `"article_header"`: the title/meta/intro group as a whole, pseudo id
  `"article-header"` — box only (side padding is a plain `ArticlePage`
  field, saved via `save_header_style` instead).

## save_quick_style

`apply_alignment_to_blocks` (default `False`) is the one destructive
exception — the JS only ever sends it after the editor confirms a warning
dialog. When true, it ALSO overwrites `alignment` on every alignment-capable
`ArticleBlockStyle` row for the article (creating rows that don't exist
yet), except any block opted out via `exclude_from_global_alignment`, AND
the title/meta/intro header group's own `title_alignment`/`meta_alignment`/
`intro_alignment` `ArticleStyle` fields (checked on their own
`"article-title"`/`"article-meta"`/`"article-intro"` rows — those three
aren't part of `page.body` so `alignment_capable_block_ids()` can't see
them). `content_font_size_multiplier`, in contrast, never touches
`ArticleBlockStyle` — it's applied purely at render time.

`reset_header` (default `False`) is the other destructive exception, same
"only sent after a confirm dialog" pattern as `apply_alignment_to_blocks`.
`content_side_padding`/`content_font_size_multiplier` only ever stack/
multiply with `header_side_padding`/`title_font_size`/`meta_font_size`/
`intro_font_size` (via `calc()` in `article_header.css`/`page_title.css`)
— they can't reset those fields back to their own defaults themselves, so
`reset_header=True` sets all seven (those four plus `title_alignment`/
`meta_alignment`/`intro_alignment`) directly from
`ArticleStyle.quick_style_defaults()`, each to its own field default rather
than to `content_alignment`'s -- those three can each have a different
default from `content_alignment` and from each other (see their own
docstrings). `apply_alignment_to_blocks`'s own header-alignment loop above
is skipped entirely whenever `reset_header` is set, specifically so it
can't immediately overwrite these three with `content_alignment`'s value
right after -- the two requests almost always arrive together (Reset also
resets the alignment control), so without that guard `reset_header`'s own
per-field defaults would never actually stick.

## save_block_style

The width/height/shadow-strength bound checks match the on-page slider's
own range (`article_block_style_mini_panel.html`) — nothing stops a direct
POST from setting an arbitrary value otherwise, and an oversized
width/height is exactly what the mobile CSS resets can't fully undo.

Several color fields treat `""` as a real, meaningful value (not "invalid,
reject it"): `text_color`/`text_custom_color` blank means "leave the text
color alone"; `box_shadow_color` blank means "keep using the theme's own
shadow color." Same convention in `save_hero_image_style`'s `shadow_color`.

## publish_page / unpublish_page

Act on the page itself (one Norwegian tree since the English overlay
switch-over; DeepL fills the English after publishing via the
`page_published` signal, which `Revision.publish()` sends too).
`can_publish`/`can_unpublish` are checked, stricter than the
`can_edit_style` every other endpoint here checks. The two-tree versions
also published/unpublished the en copy and synced fields; that went in
step 4 of the translation redesign, together with `sync_mirrored_page`.

## save_banner_style

Not `ArticlePage`-specific — looks up the plain Wagtail `Page` then
its `.specific` subtype, since `CategoryPage`,
`ArticleIndexPage`, and `StudentUnionCategoryPage` all share this one
endpoint via `BannerStyleMixin`. `banner_width_rem`/`height_rem`/
`font_size`: blank or `0` both mean "auto" — stored as `None` either way,
no distinction preserved between the two input shapes.
