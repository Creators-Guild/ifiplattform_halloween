# article_layout.css — design notes

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/article_layout.css

Covers `ifi_home_app/static/css/05_objects/article_layout.css`.

## `.article-page { display: flow-root }`

Contains floated content inside the article (hero image, floated body
images/boxes). Without it `.article-page`'s height collapses past the bottom
of a trailing float. Don't remove it as "unused".

## `.article-page { text-align: var(--content-alignment) }`

Editor-controlled default (`ArticlePage.content_alignment`). It's only an
inherited fallback: title/meta/intro have their own alignment properties
(see `article_header.md`), and most body block types set `text-align`
explicitly on themselves (`.prose--align-*`/`.heading--align-*`), which
always beats an inherited value.

## Side padding is `margin`, applied to header and body separately

- `.article-page > .article-header` and `.article-page > article` each get
  their own margin rather than padding on `.article-page` itself, so the
  hero image figure keeps its own edge-to-edge position.
- Margin, not padding: the header's accent border-bottom (and h1's own
  underline) is part of the border box. Padding on a `width:auto` block only
  shrinks the content area and leaves the border at the un-indented edge;
  margin moves the whole box, border included.
- `.article-header`'s margin is `calc(--header-side-padding +
  --content-side-padding)`: the Global editor's `--content-side-padding`
  (set on `.article-page`) stacks on top of the header's own value, never
  replaces it — same "on top of" relationship `ArticleStyle.content_side_padding`
  has with per-block padding in the body.

## Mobile (`max-width: 45rem`)

45rem (720px) is the site-wide phone breakpoint (`event_calendar.css`,
`union_card.css`, `article_multicolumn.css`, `article_image.css`,
`dropdown_menu.js`, ...). Older article rules used 480px/640px, which left
phones reporting a CSS width inside that gap with desktop editor values
still applied — keep new article mobile rules on 45rem.

Below it, editor-set side margins are dropped to 0 and `.article-page`
switches to `text-align: center` and `font-size: 1rem`, regardless of what's
configured — large padding or alignment chosen for a desktop column reads
badly this narrow.
