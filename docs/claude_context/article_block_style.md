# models/article/block_style.py — design notes

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/models/article/block_style.py

Context for future Claude sessions working on per-block article styling. Not
a human-facing doc — the code itself should read cleanly on its own; this is
where the deeper "why" lives instead of as inline comments.

## BLOCK_STYLE_DEFAULTS

- Sole source of defaults for heading/paragraph/image/multi_column blocks —
  none of them carry style fields of their own (see `article/blocks.py`:
  styling lives only in `ArticleBlockStyle`, edited on-page via editor mode).
- Used as the fallback in `_effective_block_styles()` when a block has no
  `ArticleBlockStyle` override yet, and to power the "Reset to default"
  button in the on-page block style panel (`article_block_style.js`, via
  `ArticlePage.get_context()`).
- `article_header`/`hero_image`/`toc_icon` are the exception — those are
  `ArticleStyle` fields with their own real `default=`; read from here only
  for the reset button, not for normal rendering.
- `text_color`/`text_custom_color` blank means "inherit the page's normal
  text color," not a real color of its own.
- `heading.text_shadow_enabled` defaults `False` (unlike `box_shadow_enabled`
  elsewhere, which defaults `True`) because there was no prior fixed
  text-shadow to preserve — see `ArticleBlockStyle.text_shadow_enabled`.
- `image_title`/`image_caption_body` defaults match `article_image.css`'s
  own plain defaults (0.85rem/center); `.image-title`'s bold weight stays a
  fixed CSS rule, not editable here.
- `box` is the on-page replacement for the old Wagtail 'box' block, which
  wrapped a *group* of blocks in one shared container — that grouping
  capability is gone (each block/column gets its own independent box now),
  a deliberate tradeoff for keeping box styling entirely out of Wagtail.
  `padding` = space between the box border and its content; `margin` =
  space between the box and whatever comes before/after it.
- `box.shadow_enabled`/`shadow_strength`/`shadow_color` default to
  `True`/`1`/blank specifically to reproduce the *old* fixed shadow exactly
  until an editor touches it.
- `BLOCK_STYLE_DEFAULTS["column_title"]` **aliases** (not copies)
  `["heading"]` — a multi_column column's title offers the same options as
  a heading, and this must not become a separate copy that can drift.

## _effective_box_style / _effective_heading_style

- `shadow_strength` is kept as the raw multiplier (not just derived
  offset/blur) because the on-page panel's strength slider needs that exact
  value back.
- `shadow_offset`/`shadow_blur` are precomputed here so templates don't do
  the math. Box shadow uses 2/8 (the *original* fixed shadow's own
  offset-y/blur-radius, so `strength=1` reproduces it exactly); text shadow
  uses 1/2 instead — a subtler recipe picked fresh, since no fixed
  text-shadow existed before to match.
- `font_size` is the block's own raw value (what the per-block editor
  shows/edits); `display_font_size` is that value scaled by the article's
  global `ArticleStyle.content_font_size_multiplier`. Kept as two separate
  keys so the multiplier never leaks into the raw value the mini panel edits.
- `exclude_from_global_alignment` has no defaults-dict fallback —
  `BLOCK_STYLE_DEFAULTS` already represents "no override," and "not
  excluded" (`False`) is exactly that state.

## _effective_block_styles

- An image's title (`alt_text`) and caption are boxable together as one
  unit (their own `<figcaption>`), independent of the image's own box — via
  a synthesized `{block_id}-caption` id. The title/caption *text* is
  further independent (color/alignment/font-size) via
  `{block_id}-cap-title`/`{block_id}-cap-body`, each reusing
  `_effective_heading_style`.
- A multi_column column's own title (plain text on the column struct, not a
  real Wagtail block with its own id) gets the same options as a heading
  via a synthesized `{column_id}-title` id.
- `font_size_multiplier=1.0` lets callers like `alignment_capable_block_ids`
  get every block's raw, unscaled `font_size` back — only the *shape* of
  the result matters there, not the actual sizes.

## ArticleBlockStyle model

- Deliberately **not** part of the StreamField itself — editing StreamField
  JSON in place means locating a block by id inside potentially-nested
  content and going through Wagtail's revision/publish machinery for what's
  really just a styling tweak. A plain side table keyed by `block_id`
  sidesteps all of that: no revision, no publish, no StreamField parsing,
  just an upsert.
- Tradeoff: it's a second source of truth. If a block is deleted and
  different content recreated in its place, the new block gets a new id and
  won't match any existing override (harmless — renders with stored
  defaults, same as never having been styled).
- Keyed by `translation_key`, not the `ArticlePage` row id: a leftover
  from the two-tree setup, where it was shared by the nb and en copies of
  one article. Since the English overlay switch-over there is one page per
  `translation_key`, so the two are equivalent; re-keying would need a
  data migration for no gain. English under /en/ is the same page, so
  styles apply to both languages automatically.
- `block_id` max_length is 48, not 36 (a UUID's length) — a few synthetic
  ids (e.g. `"<column-uuid>-title"`) run longer than a plain block UUID.
- `text_color` is deliberately *not* part of `_effective_box_style()`'s
  dict — unlike bg/border, it applies independent of whether the box itself
  is on.
- `text_shadow_*` mirrors `box_shadow_*`'s shape (multiplier strength,
  blank-means-theme-color) but defaults OFF since it's genuinely new (no
  prior fixed text-shadow existed anywhere), unlike `box_shadow_enabled`'s
  "on, reproducing what was already there" default.
- `box_shadow_color` blank means "keep using the page's own theme shadow
  token" (same blank-is-a-real-state convention as `text_color`) — not a
  hard-coded default like box bg/border have, since `--color-shadow` has no
  equivalent among the fixed swatch choices.
- `list_style` (article_card only): compact list row instead of a full
  card — the same layout that already auto-applies to the 3rd+ card in a
  homepage/newsbar grid on narrow screens; this makes that look available
  anywhere, on purpose.
- `height_rem`: explicit total card height; 0/blank = auto (content-driven),
  same "0 is meaningful" convention as `side_padding`/`gap`.
- `fixed_ratio` (article_card only): whether the image keeps its normal 8:5
  aspect ratio when scaling with `width_rem`. Defaults `True` (existing
  look) — an editor only needs this once they've set an explicit
  `height_rem` *and* want the image to stop scaling proportionally.
