# To fix

Last updated: 2026-09-29

Known problems found while writing the docs, waiting to be turned into
GitHub issues. When you create an issue for one, delete it here. Paths are
inside `ifiplatform/apps/ifi_home_app/` unless they start with another
folder.

## Bugs

- [ ] **The "Sync Peoply now" button runs the whole sync inside the web
  request.** If Peoply is down or slow, staff get a 500 error page after up
  to 10 seconds per union. Where: `views/event_views.py`. Fix: catch the
  error and show a message, or start the sync in the background.
- [ ] **Two "reset to default" buttons disagree** for an article's title,
  byline and intro. The block panel resets from
  `BLOCK_STYLE_DEFAULTS["article_header"]` (left-aligned, intro size 1). The
  Global editor resets from the `ArticleStyle` field defaults (centred,
  intro size 1.3). Where: `models/article/block_style.py`,
  `models/article/style.py`. Fix: pick one set of defaults.
- [ ] **Headings with the same text get the same `id`**, so the table of
  contents always jumps to the first one. Where: `_iter_toc_entries()` in
  `models/article/blocks.py`. Fix: add `-2`, `-3` to repeated ids.
- [ ] **Hand-picked union groups show retired and unpublished unions.**
  The `union_groups` cards on a `StudentUnionCategoryPage` aren't filtered
  for live, language or status. Where: `StudentUnionCategoryPage.get_context()`
  in `models/article/unions.py`.
- [ ] **The sync doesn't filter unions by language.** It loops over live
  unions in every language, so a new event's host in `related_unions` can
  point at the English copy of the union. Pages still display correctly
  (templates use `.localized`), but the stored data is inconsistent. Where:
  `management/commands/sync_peoply_events.py`. Fix: only use nb unions.
- [ ] **`--after` is read as midnight UTC**, not Oslo midnight. Where:
  `management/commands/sync_peoply_events.py`.
- [ ] **The "DRAFT" banner doesn't show on the English version** of a
  draft article. Likely cause: the banner checks `page_is_live`, which is
  the English page's own `live` flag, while Publish and Unpublish in
  Editor mode act on the Norwegian copy (`publish_target`). Where:
  `ArticlePage.get_context()` in `models/article/pages.py`,
  `templates/info_articles/pages/article_page.html`. Fix: base the banner
  on the Norwegian copy's status.
- [ ] **Menu edits don't reach the English menus.** Changes to the home
  shortcuts and to menu groups (`MenuGroup`, `MenuGroupLink`) only show on
  the Norwegian site. The English groups are separate wagtail-localize
  translations, and nothing copies changes over: pages get their synced
  fields copied on publish (the `page_published` receiver in
  `wagtail_hooks.py`), but snippets have no such hook. Editors have to
  sync each translated group by hand. Where: `models/menus.py`,
  `wagtail_hooks.py`. Fix: sync the English group when a Norwegian group
  is saved, the way pages do on publish.

## Features

- [ ] **Let admins set the Editor mode defaults in the Wagtail admin.**
  Today the defaults are hard-coded in two places: `BLOCK_STYLE_DEFAULTS`
  in `models/article/block_style.py` (per block type) and the field
  `default=` values on `ArticleStyle` in `models/article/style.py` (whole
  article). Changing them needs a developer and a deploy. Idea: a Wagtail
  settings model (`BaseGenericSetting`, under Settings in the admin) that
  holds the defaults, read by `_effective_block_styles()`, the reset
  buttons and `ArticleStyle.quick_style_defaults()`. Doing this also fixes
  the "two reset buttons disagree" bug above, since both would read the
  same values. Decide first whether changing a default should also change
  articles that already use it (they do today, since an empty field means
  "use the default").

- [ ] **Move student unions out of the info articles, like events.**
  Unions are more than information articles: they have their own events,
  calendar, board members and Peoply link. Today `StudentUnionCategoryPage`
  sits under an `ArticleIndexPage` or `CategoryPage` (for example under
  "Sosialt"). The goal is a tree like this:
  ```
  ArticleIndexPage (hub)
  ├── ArticleIndexPage (info_articles)   articles *about* unions stay here
  ├── ArticleIndexPage (news)
  ├── EventIndexPage
  └── Union index page                   one per language, all unions below it
      └── UnionPage
  ```
  What it involves:
  - **One union index page**, like `EventIndexPage`: it may only sit under
    the hub, and only once (`max_count_per_parent = 1`). The simplest way
    is to turn the existing `StudentUnionCategoryPage` into it, since it
    already lists all unions. Renaming the model to `UnionIndexPage` is
    optional and needs a migration.
  - Remove it from the `subpage_types` of `CategoryPage` and the
    info-articles index (`models/article/pages.py`,
    `models/article/unions.py`).
  - Move the existing union category page, in Norwegian and English. Check
    that the English copies move with it.
  - **Every union URL changes.** Wagtail's redirects app is installed and
    should create redirects from the old URLs automatically when the page
    is moved in the admin. Check that they appear under Settings →
    Redirects, so links from outside, such as Peoply, keep working.
  - Replace the purple union category card on category pages with a link
    or an info article that points to the unions page.
  - Update the menus, `seed_dev_data`, the breadcrumbs, and the page tree
    in `docs/architecture/overview.md` and `unions_and_tools.md`.

- [ ] **Give news and info articles their own index page types.** Today
  the hub, the info-articles index and the news index are all the same
  model, `ArticleIndexPage`, told apart by its `section` field. The goal is
  one page type per job, so the rules are in the page types instead of a
  field:
  ```
  hub                                    the site root, one per language
  ├── InfoIndexPage                      one per language
  │   └── CategoryPage → ArticlePage
  ├── NewsIndexPage                      one per language
  │   └── CategoryPage → ArticlePage
  ├── EventIndexPage
  └── UnionIndexPage                     see the item above
  ```
  What it involves:
  - New models `InfoIndexPage` and `NewsIndexPage`, each allowed only
    under the hub and only once (`max_count_per_parent = 1`). Decide what
    the hub becomes: keep `ArticleIndexPage` for it, or a small `HubPage`.
  - **Wagtail can't change the type of an existing page**, so the live
    index pages need a data migration: create the new pages (in both
    languages), move their children over, then delete the old ones. This
    is the riskiest part. Test it on a copy of the production database
    first, and take a backup before deploying it.
  - Replace everything that reads `section`:
    - `get_section_index()`, which the home page uses to find the news
      index
    - `category_section`, used by article cards
    - `ArticlePage.can_create_at()`, which blocks articles under the hub
    - the breadcrumbs, which skip the hub

    Then remove the field.
  - Check `seed_dev_data`, the menus, and the home templates (they crash
    if an index is missing, see the project rules).
  - Update `overview.md`, `articles.md` and `menus.md`.
  - Worth doing together with the unions move above, since both change
    the page tree and need page moves in production.

- [ ] **The links in a menu group look odd in the Wagtail admin.** Add a
  screenshot to the issue showing what looks wrong. What the code does
  today: each link in the "Links" list shows five full-width fields in
  this order: label, page, URL, description, prefix. There is no custom
  admin CSS. Possible improvements:
  - put page and URL side by side (`FieldRowPanel`), since only one of
    them may be filled
  - move `prefix` before `label`, the order they appear on the site
  - add help texts saying `prefix` and `description` only show on the
    home page shortcuts

  Where: `panels` on `MenuGroupLink` and `MenuGroup` in `models/menus.py`.

## Safety and cleanup

- [ ] **Some style save endpoints accept any number.** `save_quick_style`
  (`content_side_padding`), `save_header_style` (font sizes, padding) and
  `save_toc_icon_style` have no range check, unlike `save_block_style` and
  `save_hero_image_style`. Only editors can call them. Where:
  `views/article_views.py`.
- [ ] **Style rows are never cleaned up.** `ArticleStyle`,
  `ArticleBlockStyle` and `PageBannerStyle` rows stay behind when a page or
  block is deleted, and `get_or_create` writes to the database during a
  normal page view. Where: `models/article/style.py`,
  `models/article/block_style.py`, `models/page_mixins.py`.
- [ ] **Menus aren't cached.** `get_menu()` makes several queries per group
  and per link, on every page, three times on the home page. Only worth
  doing if pages feel slow. Where: `models/menus.py`.
- [ ] **Tool card markup is copied.** `article_index_page.html` and
  `article_category_page.html` write the tool card inline instead of
  including `info_articles/partials/tool_card.html` (the category version
  adds an "In <subcategory>" label). Fix: give the partial an optional
  label and include it.

## Translations

- [ ] **The Editor mode "On/Off" label is always English.**
  `static/js/article_editor_mode.js` replaces the translated text with
  hard-coded English.
- [ ] **Two union headings are Norwegian in the code.** "Programspesifikke
  foreninger" and "Andre foreninger" are Norwegian `{% trans %}` strings in
  `studentunion_category_page.html`, while every other heading is English.

## Out-of-date comments and help texts

- [ ] `ArticleIndexPage.section` help text (`models/article/pages.py`) says
  it keeps news out of the side menu. Menus don't use `section` any more.
- [ ] `deploy/systemd/sync-peoply-events.timer`: `Description=` says
  "plus 14:00", but it also runs at 16:00.
- [ ] `sync_peoply_events` and `check_peoply_union_matches` docstrings say
  the timer runs "every 6 hours", without the weekday runs.
- [ ] `ArticleStyle` help texts name `article_page.css` and
  `category_page.css`, which don't exist (the real files are
  `article_layout.css`, `article_header.css` and `page_title.css`).
- [ ] `translation/sync.py` says `publish_page` calls the sync itself. It
  relies on the `page_published` signal.
- [ ] `save_banner_style` says blank or 0 means "auto". There is no auto;
  blank falls back to a fixed default.
- [ ] The `link_peoply_organizations` docstring suggests
  `peoply_organization_id` is copied to English by the publish hook. It
  isn't a synced field; it works because `apply_peoply_match()` writes
  every language copy.
- [ ] Template comments say `.union-group-row` is in `category_card.css`
  (it's in `05_objects/category_layout.css`), and the union and tool card
  partials point to `article_models.py` (the blocks are in
  `models/article/blocks.py`).
- [ ] Some admin and model docstrings say "three" Peoply mismatch proxies;
  there are four.

## Server

From [operations/server_setup.md](operations/server_setup.md#notes-and-known-issues):

- [ ] **Gunicorn isn't in `requirements.txt`.** It was installed on the
  server by hand. Pin the server's version (`venv/bin/pip show gunicorn`).
- [ ] **Uploads over 1 MB probably fail** with "413", because Nginx has no
  `client_max_body_size`. Test with a large image in the Wagtail admin.
- [ ] **Gunicorn's timeout is 30 minutes** (`--timeout 1800`). The usual
  value is 30–120 seconds.
