# Student unions and tools

Last updated: 2026-10-09

How the student union pages and the tool pages are built: the page types,
how they are listed on category pages, the cards that show them, and how a
union is linked to Peoply so its events show up on its page. Read
[overview.md](../overview.md) first for the page tree, and
[frontend.md](../frontend.md) for how templates and CSS are loaded.
Article, category and index pages are in [articles.md](articles.md),
events and the Peoply sync in [events.md](events.md), and menus in
[menus.md](menus.md).

## What they are

| Page type | What a visitor sees | Example |
| --- | --- | --- |
| `StudentUnionCategoryPage` | A page listing every student union as a grid of round-logo cards, split into sections | "Studentforeninger" |
| `UnionPage` | One union: logo, contact links, purpose, activities, bylaws, board members, open positions, and its events | "Navet" |
| `ToolPage` | One useful tool made for IFI students: a picture, a description, screenshots and an "Open tool" button | a calendar or map website |

All three are Wagtail pages, so editors create and translate them in the
Wagtail admin. The models are in `apps/ifi_home_app/models/article/`:

| File | Holds |
| --- | --- |
| `unions.py` | `UnionPage` and `StudentUnionCategoryPage` |
| `tools.py` | `ToolPage` |
| `blocks.py` | `union_card_block()`, `union_group_block()` and `tool_card_block()` |

## Where they sit in the page tree

```
ArticleIndexPage (info_articles)
└── CategoryPage ("Sosialt")
    ├── StudentUnionCategoryPage ("Studentforeninger")
    │   └── UnionPage
    ├── ToolPage
    └── CategoryPage
        └── ToolPage
```

- `StudentUnionCategoryPage` may sit under an `ArticleIndexPage` or a
  `CategoryPage`. It can only have `UnionPage` children.
- `UnionPage` can only sit under a `StudentUnionCategoryPage`, and has no
  children.
- `ToolPage` may sit under an `ArticleIndexPage` or a `CategoryPage`, and
  has no children.

These rules are the `parent_page_types` and `subpage_types` lists on each
model.

## UnionPage

### Fields that matter

| Field | What it does |
| --- | --- |
| `logo` | Shown on the page header and on the union's card |
| `union_type` | `general` ("Open to everyone") or `program` ("Program-specific"). Shown as a badge, and decides which section the card lands in |
| `status` | `active`, `retired` or `unknown`. Decides the section on the category page and adds an icon to the title |
| `email`, `website_url`, `social_links` | The "Contact" box in the sidebar |
| `union_links` | Sign-up buttons at the top of the sidebar, each with its own label |
| `purpose`, `activities`, `vedtekter`, `vedtekter_url` | The main text sections. `vedtekter` are the bylaws |
| `sitting_members` | One block per board position (see below) |
| `member_count_intern` | Number of interns, typed in by hand |
| `peoply_organization_id` | The union's id on Peoply. See [The Peoply link](#the-peoply-link) |
| `calendar_visibility` | `auto`, `always` or `never` for the week calendar |

### Board members and open positions

`sitting_members` is a StreamField. Each `member` block is one position,
with a `role`, an optional `name`, a picture, a list of responsibilities
and an `availability` (`filled`, `open` or `opening_soon`).

Two properties read from the same list:

- `filled_positions`: every block with a `name`. Shown under "Sitting
  Members". Their responsibilities hide behind an info button.
- `open_positions`: every block whose `availability` is not `filled`.
  Shown under "Open Positions", with responsibilities shown on the card.

They are not a split. A position with a name that is also "opening soon"
shows up in both. `member_count_sitting` is just the number of
`filled_positions`, so it can't be typed in by hand.

### How the page is rendered

The template is `info_articles/pages/union_page.html`. `get_context()` adds
two things:

- `upcoming_event_month_groups`: the union's upcoming events, grouped by
  month.
- `union_calendar`: a week calendar of the union's events, or `None`.

With `calendar_visibility = "auto"`, the calendar is shown only when the
union has more than 4 events this semester (`CALENDAR_AUTO_MIN_EVENTS`).
A semester is January to June or July to December.

The calendar's Previous and Next links use `?calendar_date=`.
`js/union_calendar.js` catches the click and fetches the same URL with
`&calendar_partial=1`. `get_template()` then returns only
`info_articles/partials/union_calendar_panel.html`, and the script swaps it
in, so the page does not reload and jump back to the top.

The other scripts on the page:

| Script | Does |
| --- | --- |
| `js/union_core_sections.js` | Closes the `<details>` sections on first load on phones |
| `js/union_position_info.js` | Opens and closes the info panel on a member card |

## StudentUnionCategoryPage

### How unions are listed

`get_context()` takes the live child `UnionPage`s in the current language,
sorted by title, and splits them. The template
`info_articles/pages/studentunion_category_page.html` shows the sections in
this order:

| Order | Section | Comes from |
| --- | --- | --- |
| 1 | Editor rows | `union_groups` blocks of type `row`: several groups side by side |
| 2 | "Programspesifikke foreninger" | `program_unions`: active unions with `union_type = "program"` |
| 3 | Editor groups | `union_groups` blocks of type `group` |
| 4 | "Andre foreninger" | `other_unions`: active, not program-specific, and not picked in any editor group or row |
| 5 | "All active unions" | `active_unions`: every active union, always |
| 6 | "Old, but not forgotten" | `retired_unions` |
| 7 | "Missing in action" | `unknown_unions` |

So an active union always shows up at least twice: in "All active unions",
and in one of the sections above it. The automatic sections are hidden
when empty, except "All active unions".

### Editor groups (`union_groups`)

`union_groups` is a StreamField where editors build their own sections:

- **`group`**: a title, an optional short text, and a list of union cards.
- **`row`**: an optional title and several groups shown side by side.

Both use `union_group_block()` from `blocks.py`, and each group is
rendered by `info_articles/partials/union_group.html`.

## ToolPage

| Field | What it does |
| --- | --- |
| `description` | The main text. Required |
| `image` | The big picture at the top, and the card thumbnail |
| `image_overlay` | On: the title sits on a darkened image. Off: the image is plain and the title goes below it |
| `link` | The "Open tool" button |
| `made_by` | "Made by ..." under the title |
| `preview_images` | Up to three screenshots. Clicking one opens it large (`js/tool_preview_lightbox.js`) |

The template is `info_articles/pages/tool_page.html`. `ToolPage` has no
`get_context()` of its own.

### How tools are listed

Both `ArticleIndexPage` and `CategoryPage` put a `tools` list in their
context and show it under a "Tools" heading. The code is in
`models/article/pages.py`, next to the rest of those pages
(see [articles.md](articles.md)).

- An index page lists only its own child tools.
- A category page lists its own child tools. If the editor ticks
  `show_nested_tools`, it lists every tool anywhere below it instead, and
  those cards get an "In <subcategory>" label.

Union categories are listed on the same pages: a `StudentUnionCategoryPage`
child shows up as a purple category card next to the normal
subcategories.

## Cards

A card is a small, clickable box that links to a page. Unions and tools
each have one.

| Card | Partial | CSS | Used on |
| --- | --- | --- | --- |
| Union card | `info_articles/partials/union_card.html` | `06_components/cards/union_card.css` | the union category page, event pages, and the "Student Union Card" block in an article |
| Tool card | `info_articles/partials/tool_card.html` | `06_components/cards/tool_card.css` | the "Tool Card" block in an article |

The union card shows the logo (or an empty circle), the title and a badge.
A retired union's badge says "Closed" and the card gets the
`union-card--retired` class.

The index and category templates don't include `tool_card.html`. They write
the same tool card markup inline in the page template. If you change the
card, change it in all three places.

The article blocks (`union_card_block()` and `tool_card_block()`) are
`PageChooserBlock`s. How they fit into the article body is in
[articles.md](articles.md).

## CSS and templates

Each page loads its own list of stylesheets through a file in
`templates/css_links/` (see [frontend.md](../frontend.md)). Paths below are
in `apps/ifi_home_app/`.

| Page | Template | CSS list | Main CSS |
| --- | --- | --- | --- |
| `StudentUnionCategoryPage` | `templates/info_articles/pages/studentunion_category_page.html` | `css_links/studentunion_category.html` | `05_objects/category_layout.css`, `06_components/cards/union_card.css` |
| `UnionPage` | `templates/info_articles/pages/union_page.html` | `css_links/union.html` | `05_objects/union_layout.css`, `06_components/union/*.css` |
| `ToolPage` | `templates/info_articles/pages/tool_page.html` | `css_links/tool.html` | `05_objects/tool_layout.css`, `06_components/tool/*.css` |

The side-by-side layout of editor rows (`.union-group-row`) is in
`05_objects/category_layout.css`.

## The Peoply link

Student unions publish their events on Peoply. The site copies those
events into `EventPage`s. The link between a union here and its
organization on Peoply is the `peoply_organization_id` field on
`UnionPage`. How the sync itself works is in [events.md](events.md).

### How events reach a union page

```
UnionPage.peoply_organization_id
        │  sync_peoply_events asks Peoply for that organization's events
        ▼
EventPage  (new events get related_unions = [this union, role "host"])
        │  upcoming_events_for_union() / events_for_union_between()
        ▼
"Upcoming Events" and the week calendar on the UnionPage
```

- Only unions with a `peoply_organization_id` are synced.
- A union page shows every live event whose `related_unions` includes it,
  whatever the role. Events added by hand in the Wagtail admin show up
  too.
- Unions are matched by `translation_key`, so an event still matches the
  English copy of the union.
- Sub-events count on their own: a union tagged only on one sub-event
  still gets that sub-event.

The helper functions live in `models/event/`: the queries in `queries.py`,
the week-grid layout in `calendar_layout.py` and the date ranges in
`dates.py`. `UnionPage` imports the two `queries.py` helpers inside
`get_context()` rather than at the top of the file, because `queries.py`
imports `EventPage`, which imports the article models this file belongs to.
The others import nothing and load normally at the top.

### Setting the id

| Way | What it does |
| --- | --- |
| By hand | An editor pastes the id from the union's Peoply page into the field |
| `link_peoply_organizations` | Looks up every live nb union without an id by its title. Only an exact name or `urlId` match counts. Dry run unless you pass `--apply` |
| Django admin action | "Link selected union(s) to their matched Peoply organization" on the "Site unions with an unlinked Peoply match" list |

The command and the admin action write the id to every language copy of
the union at once (`apply_peoply_match()` in
`integrations/peoply_api.py`).

### Checking the links

`check_peoply_union_matches` compares the active nb unions with every
organization on Peoply. It runs by itself at the end of each
`sync_peoply_events`, and you can run it by hand. It finds four kinds of
problem and saves each one as a `PeoplyUnionMismatch` row, so the next
run only calls out what is new or fixed:

| Kind | Meaning | Django admin list |
| --- | --- | --- |
| `unlinked_union` | Union with no id and no exact match on Peoply | Site unions without a Peoply organization |
| `stale_link` | The id doesn't match any Peoply organization any more. The sync finds nothing for it and says nothing | Site unions with a stale Peoply link |
| `missing_org` | Peoply organization with no union here | Peoply organizations without a site union |
| `pending_link` | Union with no id, but an exact match exists | Site unions with an unlinked Peoply match |

The lists are in the Django admin and only superusers see them. From the
"Peoply organizations without a site union" list, a superuser can create
draft `UnionPage`s. The command does the same with `--create-missing`.
Either way the new page is a draft with `status = "unknown"`, for an
editor to fill in and publish.

Options for all three commands are in
[management_commands.md](../../operations/management_commands.md). When
the sync runs on the server is in
[prod_server.md](../../operations/prod_server.md).

## Where to change things

Paths are in `apps/ifi_home_app/`.

| If you want to… | Look at |
| --- | --- |
| Add a field to a union or tool | `models/article/unions.py` or `tools.py`, then `makemigrations` |
| Change which sections the union category shows | `StudentUnionCategoryPage.get_context()` and `studentunion_category_page.html` |
| Change what editors can put in a union group | `union_group_block()` in `models/article/blocks.py` |
| Change the look of a union card | `templates/info_articles/partials/union_card.html`, `static/css/06_components/cards/union_card.css` |
| Change the look of a tool card | `tool_card.html`, the tool loop in `article_index_page.html` and `article_category_page.html`, and `tool_card.css` |
| Change which tools a category lists | `CategoryPage.get_context()` in `models/article/pages.py` |
| Change a union's board member cards | `templates/info_articles/partials/union_position_card.html`, `06_components/union/union_member_card.css` |
| Change when the union calendar shows | `UnionPage.get_context()` and `CALENDAR_AUTO_MIN_EVENTS` |
| Change which events count as a union's | `_tags_union()`, `upcoming_events_for_union()` and `events_for_union_between()` in `models/event/queries.py` |
| Change how Peoply names are matched | `find_exact_match()` in `integrations/peoply_api.py` |
| Change the mismatch checks | `management/commands/check_peoply_union_matches.py`, the `PeoplyUnionMismatch` models in `models/event/peoply.py`, and `admin.py` |

## Gotchas

- **Don't rename blocks or block fields.** Wagtail stores StreamField data
  as JSON keyed by block names. That is why a board position is still
  called `member` and still has fields like `school_email`. Renaming one
  needs a migration with raw SQL.
- **Editor groups show what the editor picked.** The cards in
  `union_groups` are not filtered like the automatic sections, so a union
  that is retired or unpublished still shows up in a group until someone
  removes it.
- **A union is listed more than once on purpose.** "All active unions"
  always lists every active union, whatever the sections above show.
- **A new union's sync isn't instant.** Setting `peoply_organization_id`
  does nothing until the next `sync_peoply_events` run.
- **Only new events get the union.** The sync sets `related_unions` when
  it creates an event. After that, editors own that field, so linking a
  union later does not tag events that were already synced.
- **Some headings are in Norwegian in the code.** "Programspesifikke
  foreninger" and "Andre foreninger" are Norwegian `{% trans %}` strings,
  while the others are English. Translate them in `ifiplatform/locale/`
  (a full translations guide is planned as `shared/translations.md`).
