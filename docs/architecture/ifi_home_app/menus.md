# Menus

Last updated: 2026-10-13

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
    └── MenuGroup                     a titled list of links
        ├── MenuGroupLink             a page or an external URL
        └── MenuGroupLink
```

**`MenuGroup`**: a heading plus an ordered list of links. One row serves
both languages (see [Languages](#languages)).

| Field | Meaning |
| --- | --- |
| `title` | The heading |
| `short_title` | Optional. Used instead of `title` on narrow screens (home dropdowns and shortcut cards only) |
| `link_page` / `link_url` | Where the heading goes: a page, an external address, or neither (plain text). `clean()` stops you from setting both |
| `icon` | One of `SHORTCUT_ICONS` (`info`, `news`, `unions`, `jobs`, `events`, `tools`). Only used on shortcut cards. Blank shows the plain menu icon |

**`MenuGroupLink`**: one link in a group.

| Field | Meaning |
| --- | --- |
| `page` / `url` | Exactly one of them. `clean()` checks this |
| `label` | Link text. Blank means "use the page's own title" |
| `label_prefix` | Optional non-bold text before the label, like "Listings at" (shortcuts only) |
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
| `label_prefix`, `description` | no | no | yes |

## Editing in the Wagtail admin

Both models are under **Snippets** in the admin.

- `Menu` is registered with `@register_snippet` in `menus.py`.
- `MenuGroup` is registered in `apps/ifi_home_app/wagtail_hooks.py`,
  together with the header message and the home message board. Each row
  in its listing has an "English" button that opens the English editor.

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
3. For each slot, `_resolve_group()` reads the slot's group. On `/en/` its
   title is English by itself (see [Languages](#languages)).
4. For each link, `_resolve_link()`:
   - External URL: kept as it is, marked `external`.
   - Page: `_resolve_page()` takes `page.specific`. The link is
     **dropped** if the page is not live, or if it is a `CategoryPage`
     that is out of season (`is_visible` is false, see `active_from` /
     `active_until`).
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

There is one set of groups and menus. English is shown on top of them on
`/en/`, the same way as for pages (see
[translations.md](../shared/translations.md)):

- Group titles and short titles, and link labels, descriptions and
  prefixes, have English. URLs and icons are the same in both languages.
- `Menu` and `MenuSlot` have no text to translate.
- A page link shows the page's English title and English address on
  `/en/`. A blank link label means "use the page's title", so that is
  English too.
- Saving a group puts it and its links on the "waiting for English" list,
  and DeepL fills in the English about a minute later. To fix the English
  by hand, use the group's "English" button. The "Machine-translate menu"
  button on a `Menu` row translates all its groups and links at once.

## Gotchas

- **Don't name a field `prefix`** on a model edited in an inline panel.
  Wagtail's panel template reads the form's own `prefix`, and a field with
  that name replaces it, which breaks the whole panel. That's why the field
  is `label_prefix`.
- **An empty menu is silent.** If a `Menu` row is missing, the menu is
  simply not rendered. Run `seed_dev_data` locally to get the default
  menus.
- **English lags behind by about a minute.** Until DeepL has run, a new
  or changed group title or label shows in Norwegian on `/en/`.
- **Deleting things.** Deleting a page deletes its links
  (`on_delete=CASCADE`). Deleting a heading page leaves the heading as
  plain text (`SET_NULL`). Deleting a group removes it from every menu.
- **Columns are only an order.** `get_shortcut_columns` keeps only the
  column numbers in use, sorted, so columns 1 and 3 give two columns. The
  CSS grid has three tracks, so a fourth column wraps to a new row.
