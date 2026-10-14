# Page tree redesign (Claude plan)

Last updated: 2026-10-13

Working plan for the to_fix.md entry "Redesign the page tree: one page
type per job". Delete this file when both steps are deployed.

## Goal

```
SiteRootPage           site root; structural only, never shown
├── InfoIndexPage      once        (step 2; today ArticleIndexPage "info_articles")
│   └── CategoryPage → ArticlePage, ToolPage
├── NewsIndexPage      once        (step 2; today ArticleIndexPage "news")
│   └── CategoryPage → ArticlePage
├── EventIndexPage     once        (as today)
│   └── EventPage
└── UnionIndexPage     once        (step 1; today StudentUnionCategoryPage)
    └── UnionPage
```

Why: `ArticleIndexPage` is the root ("hub"), the info index and the news
index, told apart by `section`, which drives special cases (breadcrumbs
skip the hub, `ArticlePage.can_create_at()`, `get_section_index()`,
`category_section`). Unions have their own events, calendar, board and
Peoply link but sit inside the info articles.

## Key technique: keep page ids

Stored English (`SegmentTranslation`: specific content type + id),
`EnglishSlug`, `Site.root_page`, menu links, page choosers, revisions and
log entries all point at page ids (and some at content types). So never
recreate a page as a new type. Two tools:

- **Rename a model** (`migrations.RenameModel`) when the whole model
  becomes the new one: Django renames the content type in place (same id),
  so nothing else changes. Used for `StudentUnionCategoryPage` →
  `UnionIndexPage` and, in step 2, `ArticleIndexPage` → `InfoIndexPage`.
- **Swap a single page's type** when one model's rows split into several
  types (the hub, the news index). Raw SQL in a forward-only migration,
  one shared helper (`migrations/_page_type_swap.py`, imported by both
  steps' migrations):
  1. insert the new type's row (`page_ptr_id` = the page id, copied
     fields)
  2. delete the old type's row
  3. `wagtailcore_page.content_type_id` → new type
  4. `wagtailcore_revision.content_type_id` → new type, filtered on
     `content_type` + `object_id` (never `base_content_type`, see
     claude_context/migrations.md). Revision JSON can stay: Wagtail takes
     the type from the live page (`with_content_json`), and revisions
     find their page through these columns
  5. `wagtailcore_pagelogentry`, `wagtailcore_workflowstate` (if any),
     `ifi_home_app_segmenttranslation`: same content type update
  Before writing: read claude_context/migrations.md.

## Step 1: SiteRootPage + UnionIndexPage, unions move

Models (`models/article/`, or `models/content/` if the models-folder
reorganisation lands first):
- `SiteRootPage(Page)`: `parent_page_types = ["wagtailcore.Page"]`,
  `max_count = 1`, `subpage_types` = ArticleIndexPage (until step 2),
  EventIndexPage, UnionIndexPage. `serve()` → 404 (home is a Django view).
  `translated_fields = []` (Wagtail's own title etc. are added
  automatically; the root is never shown).
- `RenameModel` StudentUnionCategoryPage → UnionIndexPage; template
  `studentunion_category_page.html` → `union_index_page.html`;
  `parent_page_types = ["ifi_home_app.SiteRootPage"]`,
  `max_count_per_parent = 1`. Same fields (intro, general_info,
  union_groups); `rename_segment_path` not needed (paths unchanged), but
  `translated_fields.json` keys by model name → `update_translation_snapshot`
  (the snapshot test's message will say so; the stored rows don't move,
  content type id is the same).
- Swap the hub (`ArticleIndexPage` with `section="hub"`) to
  `SiteRootPage` with the helper.
- `EventIndexPage.parent_page_types = ["ifi_home_app.SiteRootPage"]`,
  `max_count_per_parent = 1`.
- Remove `StudentUnionCategoryPage`/`UnionIndexPage` and `EventIndexPage`
  from `ArticleIndexPage.subpage_types` and `CategoryPage.subpage_types`;
  drop the `"hub"` section choice.

Moving the union page: migrations don't fire Wagtail's move signals, so
redirects wouldn't be created. Instead a one-off command
`move_unions_to_root` (MovePageAction → Wagtail's Norwegian redirects +
`english_urls` English redirects), run after deploy; delete it after.
Deploy order: deploy (migrations) → run command → check Settings →
Redirects for both languages.

Code reading the hub/union category:
- breadcrumbs (`article_breadcrumbs.html`): skip `SiteRootPage` by type,
  not `section != "hub"`
- `ArticlePage.can_create_at()`: drop the hub check (articles can't be
  created under SiteRootPage by its `subpage_types`)
- `ArticleIndexPage.get_context()` / `CategoryPage`: drop
  `union_categories` and the purple union category card
  (`union_group.html`/card partials); add a link to the unions page where
  the card was, if editors want one
- `admin.py` and `check_peoply_union_matches.py` look up the union
  category to create stubs under: `UnionIndexPage.objects.live().first()`;
  `--parent-slug` goes (only one exists)
- seed (`seed_dev_data/command.py`, `unions.py`, `menus.py`): build the
  new tree; `test_seed_dev_data` + `test_english_crawl` cover it
- dashboard guide `templates/wagtailadmin/home/guide.html`: tree text

Tests:
- type-swap helper: an ArticleIndexPage with stored English, an English
  slug, two revisions and a log entry → swap → same id, `.specific` is
  SiteRootPage, English still shown under `english()`, revisions'
  `as_object()` works, reverting to the older revision works
- tree rules: SiteRootPage/UnionIndexPage/EventIndexPage only where
  allowed, only once
- move command: redirects for old /nb/ and /en/ union URLs
- existing suites (union page, peoply, menus, crawl, seed) pass

## Step 2: InfoIndexPage + NewsIndexPage, remove `section`

- Swap the news index (`section="news"`) to `NewsIndexPage` (helper).
- `RenameModel` ArticleIndexPage → InfoIndexPage (only the info index is
  left of that model).
- Parent/child rules: both under SiteRootPage, once; `CategoryPage`
  parents = InfoIndexPage, NewsIndexPage, CategoryPage; `ToolPage`
  parents = InfoIndexPage, CategoryPage.
- Replace `section` readers: `get_section_index("news")` (home view) →
  `NewsIndexPage.objects.live().first()`; `category_section` (article
  card) → nearest ancestor's type; then `RemoveField section`.
- Shared fields/template: a small abstract base for the two indexes
  (intro, general_info, banner style mixins); NewsIndexPage can reuse
  `article_index_page.html`.
- Translated places: new model names → `update_translation_snapshot`;
  SegmentTranslation rows follow via the helper / rename.
- Home templates crash if an index is missing (project rule, guards
  deliberately deferred) — keep the seed and prod tree complete.

## Both steps

- Forward-only migrations; rehearse each step on a fresh prod copy:
  restore → migrate → (step 1) move command → crawl /nb/ and /en/ (all old
  URLs work or redirect), English still shown, admin edit + revert on the
  swapped pages.
- Docs per step: overview.md tree, articles.md, unions_and_tools.md,
  menus.md, events.md (EventIndexPage parent), translations.md if needed,
  claude_context notes (article_pages, article_unions, event_models,
  translation_overlay), to_fix.md entry (remove when done).
- Open question: a ToolIndexPage only if tools stop being sorted into
  categories (UiO / Ifi verktøy).
