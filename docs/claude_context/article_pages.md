# models/article/pages.py — design notes

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/models/article/pages.py

Context for future Claude sessions. Not a human-facing doc.

## Why ArticlePage/CategoryPage/ArticleIndexPage stay in one file

Genuinely mutually referential: `isinstance` checks in `can_create_at()`/
`category` run both directions, and `get_context()` on each queries the
others live. Splitting further would need artificial local imports for no
real benefit — deliberately not split, unlike the rest of the original
`article_models.py` monolith.

## _articles_including_drafts_for_editor

Permission is checked once against the *listing* page, not per-article:
`GroupPagePermission` grants are inherited down the tree
(`PagePermissionTester.__init__`'s path-prefix matching), so anyone who can
edit the listing page can edit every article under it too — a safe lower
bound. Without this, editors would have no way to even discover/navigate to
a draft article's URL (see `ArticlePage.route()`, which already lets an
editor view one directly once they have the URL).

## ArticlePage.can_create_at

When the parent is an `ArticleIndexPage`, only allowed if that index is a
real content section, not a purely-structural "hub" index (e.g. "Artikkler",
whose children are other indexes, not articles) — `parent_page_types` alone
can only gate by page *type*, not field value.

## display_author_name

While `author` is still set: nickname (if `author_attribution` asks for it
and one exists) or real name/username. Once `author` is gone (account
deleted), falls back to the frozen `author_display_name` snapshot written
by `account_app`'s `delete_account_view`: literal sentinel `"unknown"`
renders as translated "Unknown", a real string renders as-is, blank means
this article never had a credited author (renders nothing).

## route()

A draft article stays reachable at its normal front-end URL for anyone with
edit rights on it, instead of the plain 404 `Page.route()` raises for
everyone. `subpage_types` is empty (articles have no children), so
`path_components` is only ever non-empty while routing *through* this page
toward another page — meaning the not-live branch here is the only case
that needs overriding.

## style

`style`: this article's `ArticleStyle` row (keyed by `translation_key`).
Created with defaults on first access. Cached per-instance since templates
read it repeatedly. The two-tree `publish_target` / `SOURCE_LANGUAGE_CODE`
(acting on the nb copy from an en page) went in step 4 of the translation
redesign: there is only one page now.

## get_context (ArticlePage)

- `page_has_pending_publish` is computed here rather than inline in the
  template because Django's `{% if %}` can't parse parenthesized
  expressions.
- `can_publish_page`/`can_unpublish_page` check Wagtail's publish/
  unpublish permission, stricter than the edit permission behind
  `can_edit_style`.
- `title`/`meta`/`intro` aren't part of the `body` StreamField (their
  alignment/font-size are `ArticleStyle` fields), so `_effective_block_styles`
  never sees them — their box/text-color styling is added here via fixed
  pseudo ids (`"article-title"`/`"article-meta"`/`"article-intro"`) in the
  same `ArticleBlockStyle` override table, with fallbacks written directly
  (no `BLOCK_STYLE_DEFAULTS` entry exists for these three).
- The title/meta/intro group as a whole (`"article-header"` pseudo id) is
  also independently boxable, same as `multi_column`'s grid wrapper sits on
  top of each column. Side padding isn't part of this one — see
  `header_side_padding`, a plain `ArticlePage` field driving a CSS custom
  property instead, since the header's accent underline needs its margin
  to move together with the indent.

## CategoryPage.show_nested_tools

Off by default — a category with its own subcategories (e.g. "Verktøy" ->
"UIO Verktøy"/"Ifi Verktøy") otherwise only lists its *direct* child tools,
leaving tools one or more levels down invisible on this page (still
reachable by clicking into the subcategory). Turning this on lists every
`ToolPage` anywhere below this category as one flat list.

## CategoryPage / ArticleIndexPage get_context

Both add `can_edit_style` (same permission check `save_banner_style`
enforces), `english_editor_url` and `translation_nudge`.
