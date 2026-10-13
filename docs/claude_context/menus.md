# Menus (`ifi_home_app/models/menus.py`)

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/models/menus.py, ifiplatform/apps/ifi_home_app/translation/snippets.py

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

## Translation

- `MenuGroup` and `MenuGroupLink` are both `TranslatableMixin`, so
  wagtail-localize translates group titles, link labels and prefixes.
- `Menu`/`MenuSlot` are **not** translatable. The structure is shared by
  every language, and `get_menu()` resolves each slot's group with
  `.localized`, falling back to the nb group when there's no translation.
- Page links are resolved with `.specific.localized` at render time, so a
  link stored against the nb page still points to the en page on `/en/`.
- A blank link label means "use the page's own title", which is already
  translated.
- English groups are real wagtail-localize translations of their nb group.
  They're edited in the translation editor and synced from nb, and link
  URLs and pages are synced rather than translated.
  `translation/snippets.py:link_existing_translation` registers an
  existing English copy with wagtail-localize without losing its text.
  Seeding uses it, and so does `manage.py link_menu_translations` for the
  plain copies migration `0152_menus` created. New groups just use the
  normal "Translate" button.

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
- After editing an nb group, its en translation needs a sync in
  wagtail-localize.

## Defaults

- Migration `0152_menus` builds the groups and menus from the old
  `show_in_menu` flags and slug lookups, with nb and en copies, then
  removes the flags. It is forward-only. Its en copies are only linked
  to wagtail-localize once `link_menu_translations` has run.
- `seed_dev_data/menus.py` builds the same layout for fresh databases.
