# models/article/blocks.py — design notes

Last updated: 2026-08-15
Covers: ifiplatform/apps/ifi_home_app/models/article/blocks.py

Context for future Claude sessions. Not a human-facing doc.

## Why every block is a function, not a shared instance

Wagtail block instances carry per-use bookkeeping and aren't safe to reuse
across multiple StreamField/StreamBlock definitions — several of these
blocks (`article_paragraph_block`, `article_image_block`,
`article_card_block`, etc.) are used at both the top level of an article
body *and* inside a `multi_column` column's own content
(`_body_content_blocks`), so each call must build a fresh instance.

## The `*_card_block()` family

`article_card_block`/`category_card_block`/`union_card_block`/
`tool_card_block` all follow the same shape: a `PageChooserBlock` wrapping
one page-type, reusing that content type's existing card partial
(`article_card.html`/`category_card.html`/`union_card.html`/
`tool_card.html`) rather than duplicating that markup a third or fourth
time across `article_index_page.html`/`article_category_page.html`/
`studentunion_category_page.html`.

## article_paragraph_block

A `StructBlock` (not a bare `RichTextBlock`) purely so it has somewhere to
hang the "Edit block style" trigger (alignment/font-size/side-padding,
sourced from `ArticleBlockStyle`). Historically two separate block types
existed — `'paragraph'` (bare unstyled `RichTextBlock`) and `'styled_text'`/
`'text'` (this same opt-in struct) — so adding styling didn't require an
immediate data migration; they were later merged back into one `'paragraph'`
once every paragraph got the same on-page styling (see the migration that
converts old bare-string paragraph values into this struct shape).

## multi_column's column_alignment

Deliberately stays a real Wagtail field (not moved to `ArticleBlockStyle`
like the column's side_padding/gap/weights) since it's a structural/layout
choice (vertical positioning) on a different axis entirely from left/right
weighting, with no on-page editor equivalent yet — moving it out would make
it uneditable.

## _iter_toc_entries

Multi_column column titles are treated as h3s (a smaller heading-like
label, not a real `'heading'` block). `article_body_blocks.html` builds
each entry's anchor id the same way (`slugify(text)`), so the (level, text)
pairs yielded here line up with the actual anchors on the page.
