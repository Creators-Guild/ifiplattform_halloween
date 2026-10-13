# Menus

Last updated: 2026-10-09

How the site's menus are stored, edited and turned into HTML. Menus are
Wagtail snippets. Read the [architecture overview](../overview.md) first if
you haven't. How the templates and CSS are organized is in
[frontend.md](../frontend.md). The pages that menus usually link to are
covered in [articles.md](articles.md), [unions_and_tools.md](unions_and_tools.md)
and [events.md](events.md).

## What menus are

A visitor sees three menus. All of them are on the home page, and the side
menu is also on every Wagtail page in `ifi_home_app`:

| Menu `key` | What the visitor sees | Template |
| --- | --- | --- |
| `sidemenu` | The collapsible menu on the left side | `templates/partials/sidemenu/groups.html` |
| `home_dropmenu` | The row of dropdowns at the top of the home page | `home/partials/navbar/navbar.html` |
| `shortcuts` | The big cards with icons on the home page | `home/partials/shortcuts/shortcuts.html` |

Editors pick every link by hand in the Wagtail admin. **Nothing is built
from the page tree.** A new page does not show up in any menu until an
editor adds it to one. Editors can rename groups, reorder links, point a
link at any page or external address, and reuse one group in several
menus. A step-by-step guide for editors is planned as
`contributing/content_guide.md`.

The top header (`templates/partials/header.html`) is **not** a menu in
this sense. Its links (Home, Study, Your Page, Log in and the profile
dropdown) are written straight into the template.

## The models

All four models are in `apps/ifi_home_app/models/menus.py`.

```
Menu (key = "sidemenu")               one per key, shared by all languages
└── MenuSlot (column, hide_on_mobile) the group's place in this menu
    └── MenuGroup (nb)                a titled list of links
        ├── MenuGroupLink             a page or an external URL
        └── MenuGroupLink
    MenuGroup (en)                    translation of the nb group
```

**`MenuGroup`**: a heading plus an ordered list of links. It is
translatable, so there is one row per language.

| Field | Meaning |
| --- | --- |
| `title` | The heading |
| `short_title` | Optional. Used instead of `title` on narrow screens (home dropdowns and shortcut cards only) |
| `link_page` / `link_url` | Where the heading goes: a page, an external address, or neither (plain text). `clean()` stops you from setting both |
| `icon` | One of `SHORTCUT_ICONS` (`info`, `news`, `unions`, `jobs`, `events`, `tools`). Only used on shortcut cards. Blank shows the plain menu icon |

**`MenuGroupLink`**: one link in a group. Also translatable.

| Field | Meaning |
| --- | --- |
| `page` / `url` | Exactly one of them. `clean()` checks this |
| `label` | Link text. Blank means "use the page's own title" |
| `prefix` | Optional non-bold text before the label, like "Listings at" (shortcuts only) |
| `description` | Optional small text under the label (shortcuts only) |

**`Menu`**: one row per `key`. The key is unique, so there are at most
three menus. It is **not** translatable: the same structure is used for
every language.

**`MenuSlot`**: places a group in a menu, in order.

| Field | Meaning |
| --- | --- |
| `group` | The `MenuGroup` |
| `column` | `shortcuts` only: which column the card goes in |
| `hide_on_mobile` | `home_dropmenu` only: hide this dropdown below 45rem |

Which fields each menu actually shows:

| | `sidemenu` | `home_dropmenu` | `shortcuts` |
| --- | --- | --- | --- |
| Heading link | no, the heading only opens the group | yes | yes |
| `short_title` | no | yes, on mobile | yes, if the title doesn't fit |
| `icon` | no | no | yes |
| Link thumbnail | no | yes | no |
| `prefix`, `description` | no | no | yes |

## Editing in the Wagtail admin

Both models are under **Snippets** in the admin.

- `Menu` is registered with `@register_snippet` in `menus.py`.
- `MenuGroup` is registered in `apps/ifi_home_app/wagtail_hooks.py` with
  `NorwegianFirstSnippetViewSet` (from `translation/admin_locales.py`). Its
  listing and its chooser open on Norwegian groups, so editors don't pick
  the English copies by mistake. This is the same setup as the header
  message and the home message board.

The panels are defined on each model (`panels = [...]`). Links are edited
inline on the group, and slots inline on the menu.

## From model to HTML

There is no view code and no context processor for menus. Templates ask
for them with template tags from `apps/ifi_home_app/templatetags/article_tags.py`:

- `{% get_menu "sidemenu" as menu %}` calls `menus.get_menu(key)`.
- `{% get_shortcut_columns as columns %}` calls `get_menu("shortcuts")`
  and splits the groups into columns, sorted by `column`.

Step by step, for one request:

1. A page is rendered. The side menu partial is included through the
   `sidemenu` block, which `global_base.html` puts inside
   `<aside class="sidemenu_container">`. The home page and every Wagtail
   page template (articles, categories, unions, tools, events) fill it
   with `templates/partials/sidemenu/sidemenu.html`, which includes
   `templates/partials/sidemenu/groups.html`.
2. The partial calls `get_menu`. It loads the `Menu` for the key. If it
   doesn't exist, you get an empty list and the menu is just empty.
3. For each slot, `_resolve_group()` takes `slot.group.localized`: the
   group in the visitor's language, or the Norwegian one if there is no
   translation.
4. For each link, `_resolve_link()`:
   - External URL: kept as it is, marked `external`.
   - Page: `_resolve_page()` takes `page.specific.localized`, the page in
     the visitor's language. The link is **dropped** if the page is not
     live, or if it is a `CategoryPage` that is out of season
     (`is_visible` is false, see `active_from` / `active_until`).
   - The thumbnail is the first of `logo`, `image`, `hero_image` the page
     has.
5. The group becomes a plain dict: `title`, `short_title`, `icon`, `url`,
   `external`, `show_all`, `hide_on_mobile`, `column` and `links`.
   `show_all` adds an "All" link to the heading's target, unless one of the
   links already goes there.
6. The template loops over the dicts. External links get
   `target="_blank"` and a ↗ arrow.

The dicts keep the templates simple: they never touch models or querysets.

## Languages

- `MenuGroup` and `MenuGroupLink` use `TranslatableMixin`. English groups
  are wagtail-localize translations of the Norwegian ones. Titles, labels,
  prefixes and descriptions are translated. URLs and icons are
  synchronized from Norwegian.
- `Menu` and `MenuSlot` are not translated. Slots point at a group
  (normally the Norwegian one), and `.localized` swaps in the English
  group on `/en/`.
- Page links are stored once and resolved at render time, so a link to the
  Norwegian page goes to the English page on `/en/`.
- The icon is read from the group the slot points at, and only falls back
  to the translated group's icon when that is blank.
- `manage.py link_menu_translations` registers English groups that were
  made as plain copies (by migration `0152_menus`) with wagtail-localize.
  See [management_commands.md](../../operations/management_commands.md).
  New groups use the normal "Translate" button.

The full translation workflow is planned as `shared/translations.md`.

## The `section` field

`ArticleIndexPage.section` (`hub`, `info_articles`, `news`) no longer
decides what is in a menu. Menus used to be built from `section`, a
`show_in_menu` flag on pages and hard-coded slugs. Migration `0152_menus`
turned that into editable groups and removed the flag. Today `section` is
used by `get_section_index()` (for example, the home page's news list),
breadcrumbs and article cards. Seeding and migration `0152_menus` also use
it once, to find the pages for the default groups.

## Caching

Menus are **not cached**. `get_menu()` runs on every render, with several
database queries per group and per link. The home page calls it three
times. The site's file cache (`clear_cache`) does not hold menus, so an
editor's change shows on the next page load.

## JavaScript and CSS

| File | What it does |
| --- | --- |
| `static/css/06_components/sidemenu.css` (global) | Side menu. Opens on hover or focus on desktop, on tap on touch and below 45rem. Loaded by `css_links/home_base.html` |
| `apps/ifi_home_app/static/js/sidemenu.js` | Closes the open side menu when you tap outside it |
| `static/css/06_components/dropdownmenu.css` (global) | Home dropdowns. Hover reveal on mouse devices, `.is-open` on touch. Hides the "All" link on mouse devices |
| `apps/ifi_home_app/static/js/dropdown_menu.js` | Tap to open and close dropdowns on touch devices. Also used by the header's profile dropdown |
| `.../06_components/home/home_navbar_mobile.css` | Below 45rem: hides `hide_on_mobile` dropdowns, swaps in `short_title` |
| `.../06_components/home/home_shortcuts.css` | Shortcut cards. On desktop, links appear on hover. On mobile, each card is an icon that opens a `popover` with the links |
| `apps/ifi_home_app/static/js/shortcut_fit.js` | Fits each card title: full title, then `short_title`, then smaller text |
| `home/partials/shortcuts/shortcut_icon.html` | The inline SVG for each `icon` value |

The side menu and the shortcut popovers use native `<details>` and
`popover`, so they work without JavaScript.

## Where to change things

| If you want to… | Look at |
| --- | --- |
| Add a field to groups or links | `models/menus.py`, then `_resolve_group()` / `_resolve_link()`, then the templates |
| Add a new menu | Add a key to `MENU_KEYS`, a migration, and a template that calls `get_menu` |
| Add a shortcut icon | `SHORTCUT_ICONS` in `models/menus.py` (needs a migration) and `home/partials/shortcuts/shortcut_icon.html` |
| Change which links are hidden | `_resolve_page()` in `models/menus.py` |
| Change how a menu looks | The template in the first table, and the CSS above |
| Change the default menus for a new database | `management/seed_dev_data/menus.py` |
| Change the header links | `templates/partials/header.html` (not a menu snippet) |

## Gotchas

- **An empty menu is silent.** If a `Menu` row is missing, the menu is
  simply not rendered. Run `seed_dev_data` locally to get the default
  menus.
- **English lags behind.** After an editor changes a Norwegian group, the
  English group keeps its old links and text until it is synced in
  wagtail-localize.
- **Draft translations fall back to Norwegian.** `.localized` skips pages
  that are not live, so if the English page is a draft, English visitors
  get a link to the Norwegian page.
- **Deleting things.** Deleting a page deletes its links
  (`on_delete=CASCADE`). Deleting a heading page leaves the heading as
  plain text (`SET_NULL`). Deleting a group removes it from every menu.
- **Columns are only an order.** `get_shortcut_columns` keeps only the
  column numbers in use, sorted, so columns 1 and 3 give two columns. The
  CSS grid has three tracks, so a fourth column wraps to a new row.
