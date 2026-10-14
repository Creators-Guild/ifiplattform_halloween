# To fix

Last updated: 2026-10-14

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
  for live or status. Where: `StudentUnionCategoryPage.get_context()`
  in `models/article/unions.py`.
- [ ] **`--after` is read as midnight UTC**, not Oslo midnight. Where:
  `management/commands/sync_peoply_events.py`.

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

- [ ] **Redesign the page tree: one page type per job.** Today
  `ArticleIndexPage` is the site root ("hub"), the info index and the news
  index, told apart by its `section` field, and student unions sit inside
  the info articles although they have their own events, calendar, board
  and Peoply link. The goal:
  ```
  SiteRootPage           the site root; structural only, never shown
  ├── InfoIndexPage      once
  │   └── CategoryPage → ArticlePage, ToolPage
  ├── NewsIndexPage      once
  │   └── CategoryPage → ArticlePage
  ├── EventIndexPage     once (as today)
  │   └── EventPage
  └── UnionIndexPage     once; replaces StudentUnionCategoryPage
      └── UnionPage
  ```
  What it involves:
  - **New page types**: `SiteRootPage` (only under Wagtail's root, once,
    children only the four indexes) and `InfoIndexPage`,
    `NewsIndexPage`, `UnionIndexPage` (only under `SiteRootPage`,
    `max_count_per_parent = 1`). Each declares `translated_fields`; update
    `translated_fields.json` with `update_translation_snapshot`.
  - **Wagtail can't change a page's type**, and recreating the index
    pages would give them new ids. Stored English (`SegmentTranslation`,
    keyed by content type + id), `EnglishSlug`, `Site.root_page`, menu
    links and page choosers all point at those ids. Prefer a data
    migration that swaps the type in place: add the new type's row with
    the same `page_ptr_id`, drop the old type's row, update
    `content_type` on the page and on its `SegmentTranslation` rows. Ids
    and URLs then stay the same. Forward-only; rehearse on a copy of the
    production database and take a backup first.
  - **Unions move** under `SiteRootPage`, so every union URL changes.
    Wagtail's redirects app creates redirects for the old URLs in both
    languages; check Settings → Redirects (Peoply links to union pages).
    Remove the union index from the `subpage_types` of `CategoryPage` and
    the info index, and replace the purple union category card on
    category pages with a link to the unions page.
  - **Remove `section`** and everything that reads it:
    `get_section_index()` (the home page finds the news index),
    `category_section` (article cards), `ArticlePage.can_create_at()`
    (blocks articles under the hub), and the breadcrumbs (skip the root by
    type instead).
  - Update `seed_dev_data`, the menus, the home templates (they crash if
    an index is missing, see the project rules), the dashboard guide
    (`templates/wagtailadmin/home/guide.html` describes the tree), and
    `overview.md`, `articles.md`, `unions_and_tools.md`, `menus.md`.
  - Open question: should tools get their own `ToolIndexPage` too? Today
    they sit under categories ("Verktøy").
  - Do it in two steps (root + unions first, then info/news), each with
    its own rehearsal on a copy of the production database.

- [ ] **Tidy the link fields in the menu group editor.** (The broken
  "Links" panel was fixed by renaming `prefix` to `label_prefix`.) Each
  link shows five full-width fields: label, page, URL, description,
  label prefix. Possible improvements:
  - put page and URL side by side (`FieldRowPanel`), since only one of
    them may be filled
  - move `label_prefix` before `label`, the order they appear on the site
  - add help texts saying `label_prefix` and `description` only show on
    the home page shortcuts

  Where: `panels` on `MenuGroupLink` and `MenuGroup` in `models/menus.py`.

## For future features

Problems that don't hurt today, but will once the student resource library
(documents, flashcards, images) and the wiki arrive. Plan for them before
those features launch.

- [ ] **Uploads will fill the server's disk.** The server has one 20 GB disk
  for Ubuntu, Docker images, the database and every uploaded file. A
  resource library can fill that within a few semesters. Fix: keep the
  database and `media` on a separate NREC volume mounted at a fixed folder
  (for example `/srv/ifiplatform-data`). An NREC volume can be made bigger
  later without rebuilding the server. If even that isn't enough, store
  uploads in object storage (NREC has S3-style storage) with the
  `django-storages` package.
- [ ] **Private documents can be downloaded without logging in.** Wagtail
  checks a document's privacy settings only when it's downloaded through
  Wagtail (`/documents/<id>/<name>`). The files themselves sit in
  `media/documents/`, and the web server hands out everything under
  `/media/` directly, so anyone with that direct link skips the check. This
  is already true today with Nginx, but it only matters once something is
  uploaded as login-only. Fix: make the web server refuse `/media/documents/`
  (one line in the Nginx or Caddy config), as Wagtail's docs recommend.
- [ ] **Upload size limits must be chosen on purpose.** Lecture slides and
  scanned notes can be large, and there are several limits in different
  places: the web server (Nginx today allows only 1 MB, see Server below),
  and Wagtail's image limit (`WAGTAILIMAGES_MAX_UPLOAD_SIZE`, 10 MB by
  default, not set in `ifiplatform/ifiplatform_project/settings.py`).
  Wagtail has no limit of its own for documents. Fix: decide the largest
  file we accept, set every limit to match, and write down where they are.
- [ ] **Media backups will become huge.** `deploy/backup/backup_db.sh` makes
  a full `.tar.gz` of all of `media` every day, plus one before every
  deploy, and keeps 14 days of them. That's 14 or more complete copies of
  every uploaded file on the backup volume. Fix: copy media with `rsync`,
  which only copies new and changed files, and keep the 14-day history for
  the database dumps.
- [ ] **Wiki history will fill the database.** Wagtail saves a full copy of
  a page every time someone saves it, and keeps them forever. A busy wiki
  makes many copies. Fix: decide how long history is kept, and run
  Wagtail's `purge_revisions --days=<N>` as a scheduled job.
- [ ] **Content must never be committed into a `static/` folder.** Uploaded
  material (PDFs, images, flashcard pictures) belongs in Wagtail, where it
  ends up in `media`. `static/` is only for the CSS, JS and icons that
  developers write. Files committed there are copied into every build and
  every deploy. Fix: write this rule in the contributing docs when the
  library is built.

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
- [ ] **Images with text in them can't get an English version.** Every
  image is shared between Norwegian and English, so a poster or diagram
  with Norwegian writing on it stays Norwegian on the English site.
  Possible fix: an optional "English version" image field next to images,
  used on `/en/` when set.
- [ ] **Search needs an English index.** The site has no public search
  today. If it gets one later, Wagtail's search index will only hold the
  Norwegian text, since English isn't stored as pages, so English search
  needs its own index of the translated text.
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
- [ ] `save_banner_style` says blank or 0 means "auto". There is no auto;
  blank falls back to a fixed default.
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
  value is 30–120 seconds. It was raised for machine-translating a whole
  subtree inside the web request; that now runs from the
  `ifiplatform-translate` timer, so the long timeout can probably go.
  Check that nothing else needs it (the "Sync Peoply now" button runs in
  the request too, see Bugs).
- [ ] **Local dev and production share one DeepL account.**
  `sync_deepl_glossary` replaces the glossary by name, so running it
  locally gives prod's `DEEPL_GLOSSARY_ID` a deleted glossary, and DeepL
  then fails with 404 until prod's `.env` is updated. Fix: a separate
  DeepL key for development (or none: without a key nothing is sent).
