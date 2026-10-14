# Articles

Last updated: 2026-10-13

How information articles and news are built: the three page types
(`ArticleIndexPage`, `CategoryPage` and `ArticlePage`), the StreamField
blocks editors put in an article body, and the on-page style system
(`ArticleStyle` and `ArticleBlockStyle`). Read
[overview.md](../overview.md) first for the page tree, and
[frontend.md](../frontend.md) for how templates and CSS are loaded.
Student union and tool pages are in [unions_and_tools.md](unions_and_tools.md),
events in [events.md](events.md), and the side menu in [menus.md](menus.md).

## What it is

- **Visitors** see an index page ("Informasjonsartikkler" or "Nyheter")
  with category cards, suggested articles and tools. A category lists its
  subcategories, articles and tools. An article has a title, a byline, an
  intro, an optional hero image, a table of contents and a body.
- **Editors** write the content (title, intro, body and so on) in the
  Wagtail admin, like any other Wagtail page.
- **Editors** style an article *on the page itself*, with "Editor mode":
  padding, alignment, font size, colours, boxes and shadows. These
  settings are not part of the Wagtail page. They are saved in their own
  tables and go live at once, with no draft or publish step.

## Where it sits in the page tree

All three models are in `apps/ifi_home_app/models/article/pages.py`.

```
ArticleIndexPage (section = hub)            one per language, the site root
├── ArticleIndexPage (section = info_articles)
│   └── CategoryPage
│       ├── ArticlePage
│       └── CategoryPage                    categories can be nested
└── ArticleIndexPage (section = news)
    └── CategoryPage
        └── ArticlePage
```

| Page type | May sit under (`parent_page_types`) | May hold (`subpage_types`) |
| --- | --- | --- |
| `ArticleIndexPage` | anything (not restricted) | `ArticleIndexPage`, `CategoryPage`, `StudentUnionCategoryPage`, `ToolPage`, `EventIndexPage`, `ArticlePage` |
| `CategoryPage` | `ArticleIndexPage`, `CategoryPage` | `ArticlePage`, `CategoryPage`, `StudentUnionCategoryPage`, `ToolPage` |
| `ArticlePage` | `CategoryPage`, `ArticleIndexPage` | nothing |

**The `section` field** on `ArticleIndexPage` says which part of the site
an index belongs to:

| Value | Meaning |
| --- | --- |
| `info_articles` | The information articles (the default) |
| `news` | News. The home page's newsbar takes its articles from here |
| `hub` | Structural only. It holds the other index pages, and is never a real destination |

- `get_section_index(section)` returns the live index for a section in
  the active language. The home page uses it to find the news index.
- A `CategoryPage` finds its own section with `category_section`: the
  `section` of the nearest `ArticleIndexPage` above it. Article cards use
  it to give info-article categories their accent colour.
- Menus don't use `section`. Editors pick menu links by hand, see
  [menus.md](menus.md).
- `ArticlePage.can_create_at()` stops editors from creating an article
  directly under a `hub` index. `parent_page_types` alone can only check
  the page type, not a field value.
- The hub is never shown on its own. It is the site root, but the home URL
  goes to a Django view (see [overview.md](../overview.md#from-request-to-page)),
  and the breadcrumbs skip any `hub` ancestor.

## The models and the fields that matter

### ArticleIndexPage

| Field | For |
| --- | --- |
| `intro`, `general_info` | Rich text under the title |
| `section` | See above |

`get_context()` adds `main_categories` and `seasonal_categories` (live
child categories), `union_categories`, `tools` (direct child tools), and
`suggested_articles`: the 4 newest articles anywhere below the index.

### CategoryPage

| Field | For |
| --- | --- |
| `intro`, `general_info` | Rich text under the title |
| `color` | Accent colour (`turq`, `pink`, `purple`) for the category and its articles |
| `active_from`, `active_until` | Leave both blank for a normal category. Set them for a *seasonal* one, shown under "Happening now" only between those dates |
| `show_nested_tools` | Also list tools from every subcategory below, not just direct children |

`get_context()` adds `main_subcategories`, `seasonal_subcategories`,
`union_categories`, `articles` (direct children, newest first) and
`tools`.

### ArticlePage

| Field | For |
| --- | --- |
| `intro` | Rich text shown under the title, and cut short on article cards |
| `hero_image`, `hero_image_title`, `hero_image_alt`, `hero_image_caption` | The big image at the top. How it is placed is styling, see [ArticleStyle](#articlestyle-whole-article-style) |
| `author`, `author_attribution` | Who wrote it, and whether to show their real name or nickname |
| `author_display_name` | A saved name, written by `account_app` when the author deletes their account |
| `published_date` | Required. Lists are sorted by this, newest first |
| `show_on_homepage` | Whether the home page may show this article |
| `body` | The StreamField, see [the blocks](#the-streamfield-blocks) |

Useful properties:

- `category`: the parent `CategoryPage`, or `None` if the article sits
  directly under an index.
- `display_author_name`: the name to show in the byline. Once the author
  is deleted it falls back to `author_display_name` (the value `"unknown"`
  shows as "Unknown").
- `toc_entries` and `has_headings`: the table of contents, built from the
  body.
- `style`: the article's `ArticleStyle` row.

### Drafts

- `ArticlePage.route()` lets anyone who can edit a draft article open it
  at its normal URL. Everyone else gets a 404. The template then shows a
  big "DRAFT" banner.
- Category and index listings include draft articles for users who can
  edit the listing page, so editors can find them. Article cards show a
  "Draft" badge for them.

## The StreamField blocks

The block definitions are functions in
`apps/ifi_home_app/models/article/blocks.py`. They are functions, not
shared objects, because Wagtail can't reuse one block object in several
places. `_body_content_blocks()` lists the blocks allowed at the top level
of `ArticlePage.body`.

| Block | Editors use it for | Rendered in |
| --- | --- | --- |
| `heading` | A section heading. "Level 1" to "Level 4" become `h2` to `h5` | `article_body_blocks.html` |
| `paragraph` | Rich text | `article_body_blocks.html`, `article_column_content.html` |
| `multi_column` | 1 to 4 columns side by side, each with an optional title and its own content. `column_alignment` decides where a shorter column's space goes | `article_body_blocks.html` |
| `image` | An image with optional alt text and caption | `article_image_block.html` |
| `article_card` | A card linking to another `ArticlePage` | `article_card.html` |
| `category_card` | A tile linking to a `CategoryPage` | `category_card.html` |
| `union_card` | A card linking to a `UnionPage` | `union_card.html` |
| `tool_card` | A card linking to a `ToolPage` | `tool_card.html` |

All templates are in `templates/info_articles/partials/`. Inside a column,
editors can use `paragraph`, `image` and the four card blocks, but not
`heading` or another `multi_column`.

- `paragraph` is a `StructBlock` with one `text` field, not a bare
  `RichTextBlock`, so it can carry block styles like the others.
- **Table of contents:** `_iter_toc_entries()` collects every top-level
  `heading`, plus every column title (as an `h3`). Each heading gets an
  `id` made with `slugify` from its text, and the contents list links to
  those ids.
- `union_group_block()` is in the same file but is not an article block.
  It is used by `StudentUnionCategoryPage`, see
  [unions_and_tools.md](unions_and_tools.md).

## Article and block styles

Styling lives outside the Wagtail page on purpose, in two plain Django
models, keyed by the page's `translation_key`. English is shown on the
same page, so an article looks the same in both languages, and a style
change needs no translation or publish.

| Model | File | One row per | Saved by |
| --- | --- | --- | --- |
| `ArticleStyle` | `models/article/style.py` | article | the "Global editor" panel, and the title/intro/meta, hero image and contents icon panels |
| `ArticleBlockStyle` | `models/article/block_style.py` | block in an article (`translation_key` + `block_id`) | the per-block style panel |
| `PageBannerStyle` | `models/page_mixins.py` | index or category page | the banner panel |

Nobody edits these in the Wagtail or Django admin. They are only edited on
the page, in Editor mode.

### ArticleStyle: whole-article style

`ArticlePage.style` gets or creates the row the first time it is read,
with default values. It holds:

- **Body:** `content_side_padding`, `content_alignment`,
  `content_font_size_multiplier`, and a background colour
  (`content_bg_enabled`, `content_bg_color`, `content_bg_custom_color`).
- **Header** (title, byline and intro): alignment and font size for each,
  and `header_side_padding`.
- **Hero image:** position, width, padding, and an optional box with
  colour, rounded corners and shadow.
- **Contents icon:** `toc_icon_size`.

Two things are different from the other fields:

- **Saving a new alignment overwrites blocks.** When `content_alignment`
  changes, `save_quick_style` writes that alignment into the
  `ArticleBlockStyle` row of every block that has an alignment, and into
  the title, meta and intro alignment. A block can opt out with
  `exclude_from_global_alignment`. The save button then reads "Save and
  Apply".
- **The font size multiplier never changes stored values.** It is applied
  when the page is shown, on top of each block's own size.

### ArticleBlockStyle: one block's style

One row per block that an editor has styled. Every field can be empty,
and an empty field means "use the default". The defaults are in
`BLOCK_STYLE_DEFAULTS` in `block_style.py`, one entry per block type. The
fields cover side padding, alignment, font size, width and height, column
gap and weights, text colour and shadow, and a "box" (border, background,
rounded corners, padding, margin and shadow).

`block_id` is usually the StreamField block's own id. Some ids are made up
for parts that are not blocks of their own:

| `block_id` | Styles |
| --- | --- |
| `<block id>` | a body block, or a column (a column has its own id) |
| `<column id>-title` | a column's title |
| `<image id>-caption`, `-cap-title`, `-cap-body` | an image's caption box, caption title and caption text |
| `article-title`, `article-meta`, `article-intro`, `article-header` | the title, byline, intro and the box around all three |

### How a style reaches the HTML

1. `ArticlePage.get_context()` loads every `ArticleBlockStyle` row for the
   article.
2. `_effective_block_styles()` walks the body, columns included, and
   builds a `block_styles` dictionary: `{block_id: {...}}`, with the
   saved value where there is one and the default otherwise.
3. The templates look each block up with the `lookup` filter
   (`templatetags/article_extras.py`) and write the values as inline
   `style="..."` and CSS custom properties. `_block_box_style.html` and
   `_text_color_style.html` hold the shared inline CSS for boxes and text
   colour.
4. `ArticleStyle` values are read straight from `page.style` and set as
   custom properties on `.article-page`, for example
   `--content-side-padding` and `--content-font-size-multiplier`. The CSS
   in `05_objects/article_layout.css` and
   `06_components/article/article_header.css` uses them.

On screens narrower than 45rem the CSS resets padding and header font
sizes, so a style made on a big screen can't break the phone layout.

### The save endpoints

The panels send JSON to small views in `views/article_views.py`. The URLs
are in `urls.py` under `api/articles/<page_id>/` and `api/pages/<page_id>/`.

| View | Saves |
| --- | --- |
| `save_quick_style` | The Global editor: body padding, alignment, font size multiplier, background, and "Reset all to default" |
| `save_block_style` | One `ArticleBlockStyle` row. `BLOCK_STYLE_FIELDS` lists which fields each block type may set |
| `save_header_style` | Title, intro and meta alignment and font size, and header padding |
| `save_hero_image_style` | The hero image fields on `ArticleStyle` |
| `save_toc_icon_style` | `toc_icon_size` |
| `save_banner_style` | `PageBannerStyle`, for index and category pages |
| `publish_page`, `unpublish_page` | Publish or unpublish the article from the page (both languages at once) |

Every view checks permission again with `can_edit_in_editor_mode()` (or
the publish versions), so the Editor mode switch is not a security
boundary. It only hides and shows the panels, and remembers its state in
`localStorage`.

The browser side is in `static/js/`: `article_editor_mode.js` (the
switch), `article_quick_style.js` (Global editor), `article_block_style.js`
(the block panel), `article_unsaved_changes.js` (the save bar and the
"unsaved changes" dialog) and `banner_style.js`. Changes show as a preview
at once, but are only sent when the editor presses Save in the save bar.

## How a page is rendered

There is no `urls.py` entry for these pages. Wagtail finds the page in the
tree and calls its `get_context()` and `template`:

| Page | Template | Section CSS (`section_css`) |
| --- | --- | --- |
| `ArticleIndexPage` | `info_articles/pages/article_index_page.html` | `css_links/category.html` |
| `CategoryPage` | `info_articles/pages/article_category_page.html` | `css_links/category.html` |
| `ArticlePage` | `info_articles/pages/article_page.html` | `css_links/article.html` |

- All three extend `home_base.html` and use the side menu from
  `templates/partials/sidemenu/sidemenu.html`.
- For editors (`can_edit_style` in the context), `page_css` also loads
  `css_links/article_editor.html`, and the template includes the panels
  and scripts.
- `article_page.html` includes `article_body_blocks.html` for the body.
  For a `multi_column`, that includes `article_column_content.html` for
  each column. Both hand images to `article_image_block.html` and cards to
  the card partials.
- `article_card.html` is also used by the home page newsbar and by event
  pages.
- Index and category pages show the title through `page_title_banner.html`,
  with an optional coloured banner from `PageBannerStyle`
  (`BannerStyleMixin` in `models/page_mixins.py`).

## Translations

There is one Norwegian page tree; English is shown on the same pages. How
that works is in [translations.md](../shared/translations.md). What is
special here:

- **Styles, publish and unpublish** apply to both languages at once,
  since there is only one page.
- `TranslationWarningMixin` sets `needs_translation`, which shows a
  "This page hasn't been translated yet" note to visitors when some of the
  English is missing. `EditorModeMixin.translation_nudge()` shows editors
  a "missing" or "out of date" banner, and `english_editor_url()` links
  Editor mode to the English editor.

## Where to change things

| If you want to… | Look at |
| --- | --- |
| Add a field to an article, category or index | `models/article/pages.py`, then `makemigrations` |
| Add or change a body block | `_body_content_blocks()` in `models/article/blocks.py`, and `article_body_blocks.html` (and `article_column_content.html` if it can go in a column) |
| Make a new block styleable | `_effective_block_styles()` and `BLOCK_STYLE_DEFAULTS` in `block_style.py`, `BLOCK_STYLE_FIELDS` in `views/article_views.py`, and `article_block_style.js` |
| Change a style default | `BLOCK_STYLE_DEFAULTS` (blocks) or the field's `default=` in `models/article/style.py` (whole article) |
| Change what the index or category page lists | `get_context()` of that model in `pages.py` |
| Change how an article looks | `article_page.html`, and the CSS in `static/css/05_objects/article_layout.css` and `06_components/article/` |
| Change the article card | `info_articles/partials/article_card.html`, `06_components/cards/article_card.css` |
| Change the table of contents | `_iter_toc_entries()` in `blocks.py`, `article_page.html`, `06_components/article_toc/`, `static/js/table_of_content.js` |
| Change who may use Editor mode | `EditorModeMixin` and `editor_mode_allowed()` in `models/page_mixins.py` |

All paths are inside `apps/ifi_home_app/`.

## Gotchas

- **Removing or renaming a block type** in `_body_content_blocks()` needs
  a migration that reads and writes the body with raw SQL. Wagtail stores
  old bodies in revisions too.
- **`models/article_models.py` must stay.** It only re-exports names from
  `models/article/` and `page_mixins.py`, but old migrations and many
  imports use that exact path.
- **Style rows are never cleaned up.** Deleting a block or a page leaves
  its `ArticleStyle` and `ArticleBlockStyle` rows behind. Copying a page
  in Wagtail gives it a new `translation_key`, so the copy starts with
  default styles.
- **Changing the number of columns** in Wagtail makes a saved
  `column_weights` override stop matching, and the columns go back to
  equal widths.
- **Headings with the same text** get the same `id`, so the contents
  list jumps to the first one.
- **Seasonal categories** are hidden from listings outside their dates,
  but their URL still works.
- The home templates crash if the info-articles or news index is missing
  in a language. This is known, and the fix is on hold.
