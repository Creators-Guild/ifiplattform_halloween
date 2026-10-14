# Menus (`ifi_home_app/models/menus.py`)

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/models/menus.py

The sidemenu, the homepage navbar dropdowns ("home dropmenus") and the
homepage shortcut cards are all editor-curated snippets. None of them is
derived from the page tree.

- **`MenuGroup`**: a titled, ordered list of `MenuGroupLink`s. Each link is
  a page on the site *or* an external URL. The group's own heading can link
  to a page (`link_page`) or an external URL (`link_url`), or to neither,
  in which case it renders as plain text. `icon` picks one of the fixed
  `SHORTCUT_ICONS`: inline SVGs in `home/partials/shortcuts/shortcut_icon.html`,
  drawn in `currentColor`. It is shown on the group's homepage shortcut
  card; blank keeps the plain menu icon. `get_menu()` reads it from the nb
  group the menu slot points at, so editors set it once and English
  follows without a translation sync.
- **`Menu`**: one row per `key` (`sidemenu`, `home_dropmenu`,
  `shortcuts`), listing groups in order through `MenuSlot`s. A slot's
  `column` is only used by `shortcuts`, and `hide_on_mobile` only by
  `home_dropmenu` (it becomes `.dropdown-menu--hide-mobile`, see
  `home_navbar_mobile.css`). One group can sit in several menus.

## Why not tree-driven

Before this change, the menus came from three mechanisms:
- a `show_in_menu` flag on `CategoryPage`/`UnionPage`
- sections found by `ArticleIndexPage.section` name
- nb-slug lookups in `home_views.py` and `article_tags.py` (`ifi-verktøy`,
  `ny-ifi-student`, `studentforeninger`, `hjelp`)

Any restructure or slug rename broke them silently. A tree-driven redesign
(sections under the site root plus per-page flags) was considered and
rejected as too implicit for editors. Explicit picks are easier to explain
and don't depend on where pages sit.

## label_prefix, not prefix

Renamed in migration 0159: a form field called `prefix` shadows
`form.prefix` in Wagtail's inline panel template
(`{{ child.form.prefix }}` builds the child's ids; Django templates try
`form["prefix"]` first, a BoundField), so the Links panel rendered its
own markup as text. The migration moves stored English
(`rename_segment_path`). `get_menu()` still
hands templates a `"prefix"` key.

## Translation

- Since the English overlay switch-over there is one set of groups (nb).
  `MenuGroup.translated_fields` (title, short_title) and
  `MenuGroupLink.translated_fields` (label, description, label_prefix) show in
  English under /en/ by themselves (see `translation_overlay.md`); each
  link is its own object in the English tables, and the English editor of
  a group lists its links too.
- `Menu`/`MenuSlot` aren't translated: one structure for every language.
- Page links resolve to the page itself; under /en/ its title and address
  are English automatically. A blank link label means "use the page's own
  title", so it's English too.
- `MenuGroup`/`MenuGroupLink` are still `TranslatableMixin` (wagtail-localize
  needed it); nothing uses their locale any more.

## Resolving (`get_menu(key)`)

`get_menu()` returns plain dicts so the templates stay simple. It skips:
- links to pages that aren't live
- off-season `CategoryPage`s (`is_visible`)

A deleted page's links disappear on their own
(`MenuGroupLink.page` is `on_delete=CASCADE`). A deleted heading page
leaves the heading as plain text (`SET_NULL`). Thumbnails come from the
first of `logo`, `image`, `hero_image` that the page has.

## Editor upkeep

- A new page doesn't appear in any menu until someone adds it to a group.
- After editing a group, DeepL fills its new English on save (the English
  editor shows and fixes it).

## Defaults

- Migration `0152_menus` builds the groups and menus from the old
  `show_in_menu` flags and slug lookups, with nb and en copies, then
  removes the flags. It is forward-only. The switch-over command turned
  the en copies' text into stored English (paired by place).
- `seed_dev_data/menus.py` builds the same layout for fresh databases.
