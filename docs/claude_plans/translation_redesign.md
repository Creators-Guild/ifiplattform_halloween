# Translation redesign (Claude draft — reference only)

Last updated: 2026-10-13

> **Note:** This is a Claude-authored plan kept in `docs/claude_references/`
> (see [readme.md](readme.md)). It is the working plan for the
> `task/nb-as-source-of-truth` branch, not a finished doc. Once built, the
> real explanation goes in `docs/architecture/shared/translations.md`.

Redesign: one Norwegian page tree, English as a translation overlay.

**Status: done and in production (2026-10-13).** All steps built,
deployed and switched; the one-time `switch_to_english_overlay` command
was deleted afterwards. The real explanation for people is
`docs/architecture/shared/translations.md`. Only "Later phases" remain,
as optional extras.

## In one minute

- **Problem:** English is a second full copy of every page and snippet
  (wagtail-localize). Two copies drift apart, and a lot of sync code and
  workarounds exist only to hold them together.
- **Solution:** only Norwegian pages and snippets exist. English is stored
  as translated text pieces. When a page is shown under `/en/`, reading a
  field (`page.title`, `page.body`…) automatically gives the English —
  developers write normal code, nothing to remember.
- **Result:** one page, one tree, one publish status. English can't drift
  from Norwegian because there is nothing separate to drift.
- **DeepL** translates automatically on publish; editors' fixes survive
  until the Norwegian text under them changes.
- **English addresses** use English slugs (`/en/freshers-week/`); today's
  English slugs are kept, so most English links don't change.
- **wagtail-localize can be removed later** by rewriting one file: the
  stored data, hash and DeepL client are our own.

## Bugs this removes

| Bug | Why it happens today |
|---|---|
| DRAFT banner missing on English | en page has its own `live` flag |
| Menu edits don't reach English | snippets have no sync hook |
| Peoply events point at English unions | sync picks whichever locale copy comes first |
| Home crashes if an index page is missing in one locale | two trees must match |
| Peoply unpublish leaves English live | only nb is unpublished |
| Article cards link to Norwegian pages on `/en/` | `article_body_blocks.html` has no `.localized` |
| English union page lists unions twice | nb ids compared with en ids (`unions.py:438-450`) |

Plus workarounds that go away: style rows re-keyed to `translation_key`,
`translation_key` dedup in events/Peoply, `sync_locale_trees` calls,
seed `fix_tree()`.

## Decisions

| Topic | Decision |
|---|---|
| Source of truth | Norwegian only; English always mirrors it |
| Languages | Norwegian + English only, for good; no third-language support built |
| English content | DeepL + occasional human fixes |
| Addresses | English slugs in this build (`EnglishSlug` table); existing English slugs carried over |
| Where English text is stored | our own `SegmentTranslation` table (translations only; Norwegian pages stay in Wagtail's normal tables) |
| How English reaches the screen | automatic "translate on read", per field (option B) |
| wagtail-localize | kept only for splitting fields into pieces, inside `page_segments.py`; stored format, hash and DeepL client are ours, so it can be removed by rewriting that one file |
| Auto-translate | on publish + nightly catch-up; superuser on/off setting |
| Images | shared between languages (known gap, in `docs/to_fix.md`) |
| Deploy | only after a clean rehearsal on a copy of the prod database |

## How it works

```
Visitor opens /en/freshers-week/  (GET)
  → middleware: English is active for this request
  → routing finds the one (Norwegian) page whose English slug is
    "freshers-week" (its Norwegian slug is "fadderuke")
  → template reads page.title
       → translated field: English active?
            ├─ first read on this page: stored_translations.lookup(page)
            │     → this page's rows (1 query), remembered on the page
            ├─ page_segments: Norwegian title → matching English
            └─ returns "Freshers' week"   (only the title is translated)
  → template reads page.body → same, for the body only
  → menus, cards, lists: same mechanism, automatically
  → links get /en/<English slugs>/ addresses automatically
```

- `WAGTAIL_I18N_ENABLED = False`: Wagtail stops deciding the language;
  Django's `i18n_patterns` (`/nb/`, `/en/`) does. Links then follow the
  visitor's language (checked in `wagtail/models/pages.py` ~L1383).
- Missing English → that piece stays Norwegian.
- **English is only active when displaying:** GET/HEAD requests under
  `/en/` and English previews. Admin, POST/AJAX (editor-mode buttons),
  commands and the worker always see Norwegian.
- **English can never reach the database** (guard A, chosen after step 0):
  1. while English is on, writes (INSERT/UPDATE) to pages, page types,
     snippets, menu links and revisions are **refused** — every path
     (`save()`, revisions, `update()`, `bulk_update()`, ones nobody thought
     of) fails loudly instead of silently storing English
  2. when Django copies a field's value back onto the object
     (`refresh_from_db()`, loading a deferred field, and `full_clean()` /
     `clean_fields()`, which every `save()` runs first), it reads
     Norwegian, so the object's Norwegian values stay Norwegian in memory
  3. Wagtail's own `Page` class gets translated `title`, `seo_title` and
     `search_description`, so plain `Page` objects (`get_children()`,
     breadcrumbs, `get_parent()`) show English too, under the same guard

## The translation module

Five files in `ifi_home_app/translation/`. Only `page_segments.py`
imports wagtail-localize (a test fails if any other project file does). Normal site code calls none of them —
translation happens when fields are read. Parameters are called `page`,
but menus, menu links and messages work too (docstrings say "page, menu
group or message").

| File | Job | Main functions |
|---|---|---|
| `page_segments.py` | split a field into text pieces, put English back | `Segment`, `extract_segments(page, field)`, `apply_translations(page, field, translations)` |
| `stored_translations.py` | the only code that reads/writes the `SegmentTranslation` table (plain functions, not a class) | `lookup(page)`, `save_human(...)`, `save_machine(...)`, `cleanup()` |
| `english_overlay.py` | the automatic part | `TranslatedFieldsMixin`, `english_active()`, `raw_norwegian()`, `block_english_writes`, `translation_status(page)` |
| `auto_translate.py` | DeepL in the background | `fill_missing(page)`, `request_english(page)`, `translate_waiting()`, nightly catch-up |
| `english_urls.py` | English slugs: storing, routing, building `/en/` links | `english_slug(page)`, `set_english_slug(...)`, `english_url_path(page)`, `find_child(parent, slug)` |

`translation/deepl.py` becomes a plain DeepL client (direct HTTP with
`requests`, which it already uses), no longer a subclass of
wagtail-localize's `DeepLTranslator`.

### `SegmentTranslation` (new model, `models/translation.py`)

One row = "at this place on this page, this Norwegian text is this English
text".

| Field | Meaning |
|---|---|
| `content_type` | type of page, menu or message |
| `object_id` | which page/snippet (its normal database id) |
| `segment_path` | where on it, e.g. `body.<block-id>.text` |
| `norwegian_text` / `norwegian_hash` | the Norwegian text, and its hash for lookups |
| `english_text` | the English |
| `source` | `deepl` or `human` |
| `translated_by` | person who last wrote/fixed it (FK User, `SET_NULL`; empty for DeepL) |
| `has_error` / `error` | text couldn't be put back into the page |
| `created_at` / `updated_at` | |

- Unique on (`content_type`, `object_id`, `segment_path`,
  `norwegian_hash`). Note: a place is **not** unique on its
  own — a rich text field is split into several pieces sharing one path —
  so rows are always matched on place **and** Norwegian text.
- Keyed by `object_id`, not `translation_key`: `translation_key` belongs to
  Wagtail's language system, which is switched off. With `object_id`,
  snippets can drop `TranslatableMixin` later. The migration converts
  keys to ids (after migration each key has exactly one Norwegian object).
- **The stored format is ours.** `norwegian_text` uses the same written
  form as wagtail-localize today (links as placeholders, e.g.
  `<a id="a1">`), and `norwegian_hash` is `uuid5` with the same namespace,
  so migrated English matches (otherwise everything would be
  retranslated). But the namespace is a constant **in our code**, and
  golden test files (input page → exact expected pieces and hashes) pin
  the format as our own. A replacement for wagtail-localize must pass the
  same golden tests; no data changes.
- DeepL writes are **insert-only**, done by the database in one step
  (`INSERT … ON CONFLICT DO NOTHING`): DeepL only fills places with no
  row yet and never touches an existing row. Human saves always replace.
  Whatever the order, the human text wins; parallel jobs are harmless.
- Human fix → same row: new `english_text`, `source = human`,
  `translated_by` = user.
- Norwegian changes → new row; the old one stays until cleanup (kept so
  it can later be shown as a suggestion, see Later phases).
- User deleted → `translated_by` empties, `source = human` stays (text
  still protected).
- **Read-only list in the admin for superusers** (needed for debugging):
  every row with page, place, Norwegian, English, source, fixed by, error.
  Filters (source, has error, page type) and search (Norwegian and
  English text). No editing here; English is changed only in the English
  text editor. Built with Wagtail's standard model listing (one short
  file).
- Later: full author + editors history instead of `translated_by`.

**Cleanup** (`stored_translations.cleanup()`, called by the nightly job
(`translate_english --nightly`; no separate command was built);
compared with the **published** page, so drafts never delete anything):
1. page/snippet deleted → delete its rows
2. place no longer on the page → delete its rows
3. old rows at a place → delete old `deepl` rows; keep only the newest old
   `human` row (for the later suggestion feature)

### `page_segments.py`

- `Segment`: our own dataclass (`path`, `norwegian_text`, `norwegian_hash`).
  wagtail-localize's segment classes never leave this file. The hash is
  computed by our own `segment_hash(text)`, not theirs.
- `extract_segments(page, field=None)`: list of `Segment` for one field
  (or the whole page when `field` is omitted — used by status, the
  editor and DeepL). Text only; page links, images, URLs and emails stay
  Norwegian. Uses wagtail-localize's per-field extractors
  (`StreamFieldSegmentExtractor`, rich-text string extraction), always
  reading the **raw Norwegian** values.
- **Only text for people is translated.** By default wagtail-localize
  translates every text field, including `peoply_organization_id`,
  `external_uid`, colour codes and `slug`. So:
  - every page type and snippet declares `translated_fields`
  - a small exclude list covers technical fields inside body blocks
  - `slug` is never translated as a text piece (English slugs have their
    own table, see `english_urls.py`)
  - a test fails if a model has no list
- **Rename protection (automatic, no docs needed):** a snapshot file
  (`translation/translated_fields.json`) lists every translated place
  pattern per model, including block fields (e.g. `ArticlePage: title,
  intro, body→image→caption`). A test compares it with the models and
  fails — locally and in CI on the pull request — when one disappears.
  The failure message says what to do: if renamed, add
  `rename_segment_path(apps, "ArticlePage", "caption", "image_caption")`
  to the migration (ready-made helper that moves the stored English); if
  removed on purpose, run `manage.py update_translation_snapshot`.
- `apply_translations(page, field, translations)`: `translations` is a
  dict `{Segment: English text}` (keyed by place + Norwegian text, since a
  place alone isn't unique). Returns the **English value of that one
  field** (text, rich text HTML or StreamField value), built from a
  **deep copy** of the Norwegian value (wagtail-localize edits in place).
  The page object itself is never modified.

### `stored_translations.py`

- `lookup(page)` → all of that page's rows (one query), remembered on the
  page object for the rest of the request. Matching to the current
  Norwegian text (place + hash) happens per field when it's read. Whole
  rows (`english_text`, `source`, `has_error`, `translated_by`) because
  fields, status, banner and editor need different columns.
- `save_human(page, segment, english, user)`: create or update, for the
  `segment` (place + Norwegian text) the editor saw.
- `save_machine(page, segment, english)`: insert only if no row exists.
- `cleanup()`: the three cleanup rules above.
- Nothing else in the project queries `SegmentTranslation` directly.

### `english_overlay.py`

- `TranslatedFieldsMixin` (part of the shared base mixin for page types,
  translatable snippets and `MenuGroupLink`): for every field in the
  model's `translated_fields`, installs a **translated field**
  (a subclass of Django's field attribute). Reading it returns English
  when `english_active()` and not in raw mode, otherwise the stored
  Norwegian value. **Per field:** reading `title` never translates
  `body`. Results remembered on the object for the request.
- **Wagtail's own `Page` class** gets the same translated fields for
  `title`, `seo_title` and `search_description`, installed once at
  startup (`AppConfig.ready()`), because `get_children()`, breadcrumbs and
  `get_parent()` return plain `Page` objects (step 0). Its
  `refresh_from_db()`, `full_clean()` and `clean_fields()` are wrapped in
  `raw_norwegian()` there too. Tests
  fail with fix instructions if a Wagtail upgrade changes what this
  relies on.
- **It must catch every read.** Django stores loaded values directly on
  the object, and a normal descriptor (one with only "get") is then
  skipped. The translated field is a *data descriptor* (both "get" and
  "set") that wraps the original one (Django's, or Wagtail's StreamField
  `Creator`). Proven in step 0.
- `english_active()`: true only during display — set by a middleware for
  GET/HEAD requests under `/en/`, and by the English preview mode. Always
  false in the admin, POST/AJAX, commands and the worker. Separate from
  Django's language (in the admin that's the editor's menu language).
  Stored in a `contextvars.ContextVar` (correct for threads and async
  alike) and reset with its token in a `finally` block after every
  request, **even on errors** (server processes reuse state between
  visitors).
- `raw_norwegian()`: context manager forcing stored values. Wraps
  `refresh_from_db()` (which also runs when a deferred field is loaded),
  `full_clean()` and `clean_fields()` (step 1: `save()` runs them first):
  step 0 showed that without it, Django copies the *English* value into
  the object's Norwegian slot. `page_segments` also reads through it.
- `block_english_writes`: a database wrapper (Django's
  `connection.execute_wrapper`, added to every connection via the
  `connection_created` signal) that refuses INSERT/UPDATE on translated
  tables while `english_active()`. The table list is built from the
  installed models, never written by hand. English is only on during
  display and previews, which never save, so this only ever fires on a
  bug. Proven in step 0 for `save()`, `save_revision()`, `update()`,
  `bulk_update()` and snippet saves; reads and other tables unaffected.
  This replaces wrapping `save()`/`save_revision()`/serialization.
- Works the same on objects from any query, `get_children()`,
  `.specific` (a re-fetched object is translated too) and menus — no
  call sites to change.
- `translation_status(page)`: counts (total, deepl, human, missing,
  errors) for nudges, dashboard, banner, editor.
- No cache in this build (see Later phases).

### `english_urls.py` and `EnglishSlug`

English addresses use English slugs: `/en/student-life/freshers-week/`
instead of `/nb/studentliv/fadderuke/`.

**Storage:** a small table `EnglishSlug` (one row per page: `page`
one-to-one, `slug`, `source` deepl/human, `updated_by`, `updated_at`).
Its own table, not a page field, so the worker can set it without making
a page revision, and a later publish of an old draft can't wipe it.

**Rules:**

| Situation | What happens |
|---|---|
| Page's title first gets English | slug = slugified English title, set once by `fill_missing` |
| English title changes later | slug stays (stable addresses, same as Wagtail's own slug after publishing) |
| Editor changes the slug (English editor) | new slug; old address gets a redirect |
| Page has no English slug yet | Norwegian slug used in the English address |
| Two sibling pages would get the same slug | `-2`, `-3` added; must also not equal a sibling's Norwegian slug (that's the fallback address) |
| Page moved | old English address gets a redirect (same as Wagtail does for Norwegian) |

**Redirects** use Wagtail's built-in redirects app (already installed),
the same table as Norwegian redirects. One place for all redirects.

**Routing** (`route()` on the shared mixin, under `/en/`): for each part
of the address, find the child whose English slug matches; if none, the
child whose Norwegian slug matches, and redirect to its English address
if it has one.

**Building links** (`get_url_parts()` on the shared mixin, under `/en/`):
the English slugs of the page and its ancestors. **The path follows the
address prefix** (Django's active language), not `english_active()`: any
link built under `/en/` uses English slugs, also on POST/AJAX where
English text is off, so every `/en/` link is valid. With Wagtail's
language system off, the prefix already follows the active language
(step 0). All current English
slugs are loaded in **one query, once per request** (a few hundred short
rows), so lists of cards don't cause a query per link.

## Wiring into the site

All page types and translatable snippets share one base mixin.

| Where | Change |
|---|---|
| Visited page, menus, cards, lists, breadcrumbs, `get_children()` | **nothing** — translated automatically when fields are read |
| Previews | `preview_modes` Norsk / English; English mode turns `english_active()` on |
| `.localized` calls (`menus.py:182,214`, `event/pages.py:280-325`) | removed (they return the page itself with i18n off) |
| Card blocks, `union_groups`, `related_unions`, `location_articles` | nothing — the linked nb pages show English automatically (fixes two bugs) |
| Listings filtering `locale=Locale.get_active()` (`article/pages.py`, `unions.py:429`, `event/pages.py:81`, `article_tags.py:35`, `site_tags.py:23`, `home_views.py:35-54`) | filter removed (only Norwegian rows exist after migration) |
| Page routing and links | `route()` / `get_url_parts()` on the shared mixin call `english_urls` (see above) |
| Language switcher (`site_tags.translated_page_url`) | same page's address in the other language (`english_url_path(page)` / Norwegian `url`) |
| Sitemap (`core_app/sitemaps.py`) | `/nb/` and `/en/` (English slug) per page |
| Caching | none today, none added in the first version |

**Hide wagtail-localize's admin UI** (required): remove its "Translate
this page", sync buttons, locale switcher and editor links via hooks. A
test checks they're gone. Wagtail's own locale UI disappears with i18n off.

## Automatic translation

- **On publish** (pages) and **on save** (snippets): mark the object
  "waiting for English". Only new/changed pieces go to DeepL. Not on draft
  saves. Pages hook the `page_published` **signal**, not the edit view, so
  scheduled publishing, workflow approvals, Peoply sync and commands
  trigger it too (same pattern as `wagtail_hooks.py:93` today). Until the
  switch-over only Norwegian-locale objects are marked.
- **Queue: a small table + a systemd timer** (decided 2026-10-12 in step 2;
  replaces `django-tasks` + `db_worker`, whose database backend moved to a
  separate 0.x package). `WaitingForEnglish` holds one row per object
  waiting; `manage.py translate_english` runs every minute
  (`ifiplatform-translate.timer`, same pattern as the backup timer),
  translates what's waiting one object at a time and deletes the row.
  Survives restarts (rows in the database); failures recorded on the row
  (`attempts`, `last_error`) and retried with a growing wait (2, 4, 8 …
  up to 60 minutes). English appears up to about a minute after
  publishing. No always-running service.
- **Nightly job** (`translate_english --nightly`, its own timer): mark
  everything with missing English as waiting and translate it (only when
  auto-translate is on), then run cleanup (always).
- **Keeps:** glossary, `translation/deepl.py` (rewritten as our own
  client; wagtail-localize's subclass stays as a thin adapter over it until
  the switch-over), `DEEPL_CALL_DELAY_SECONDS`,
  `_clear_stale_glossary_translations` (only `deepl` rows).
- **"Machine-translate now"** button in the English editor: translates
  that object right away (manual fallback, works when auto-translate is
  off).
- **Previews** never call DeepL.
- **Local dev / tests:** no DeepL key → nothing is marked waiting and no
  DeepL calls happen; tests swap in a fake client.

**Admin setting** (`wagtail.contrib.settings`, built in;
`TranslationSettings.auto_translate`, default on, superusers only):

| State | Behaviour |
|---|---|
| On | DeepL on publish + nightly |
| Off | no automatic DeepL; manual button still works |
| Switched back on | the nightly job fills in what's missing |

## "Not translated yet" banner

One rule: **some English is missing (or has an error) → banner shown,
unless the object has been waiting for English less than 10 minutes**
(its `WaitingForEnglish` row).

This covers every case without a list of exceptions:

| Situation | Result |
|---|---|
| Just published, job running | hidden (pending) |
| DeepL failed / quota / piece with error | shown |
| English preview of a draft with new text | shown (previews never call DeepL) |
| Auto-translate off | shown |
| Worker down or job lost | shown after 10 min |
| Fully translated | hidden |

## English text editor

Admin view (also reachable from Editor mode): one row per piece —
Norwegian | English | deepl/human | outdated. Saving calls `save_human()`.
For pages, the English slug is editable at the top (`set_english_slug`).
Replaces wagtail-localize's editor (which needs an English page).

- Each fix is saved against **the Norwegian text the editor was looking
  at** (the form carries each piece's `norwegian_hash`), never the
  current text at save time. If the Norwegian changed while they were
  editing, the fix attaches to the old text and the new text gets DeepL.
  (Telling the editor and offering their fix as a suggestion: Later
  phases.)
- Why the human wins only for the same Norwegian text: rows are tied to
  the exact Norwegian they translate, so a fix can never outlive the text
  it belongs to; letting DeepL win would erase fixes every run without
  making Norwegian any more the source.

## Migration (forward-only)

1. **Copy English into `SegmentTranslation`**
   - from wagtail-localize's tables (they record which Norwegian each
     English translates): manual → `human` + `translated_by`;
     machine → `deepl`; technical fields not copied
   - fallback for English typed straight into English pages: pair with the
     nb page by block id; listed in the report (not provably current)
   - menu links: wagtail-localize stored them under the `MenuGroup`
     (`links.<link key>.label`); they're copied as rows of the
     `MenuGroupLink` itself (its own content type + id, path `label`),
     since each link now translates its own fields
   - `translation_key` → `object_id` of the one Norwegian object
2. **Copy English slugs:** each English page's current slug → an
   `EnglishSlug` row for its Norwegian page (`source = human`, since
   someone chose or accepted it). Sibling clashes get `-2`, listed in the
   report.
3. **Repoint stray English references** to nb (known: Peoply
   `related_unions`, raw SQL). Fails if any remain. Style rows: nothing to do.
4. **Redirects** only for old English addresses that changed (clashes,
   pages where the English tree differed). Most stay the same.
5. **Delete** English pages, snippet copies, aliases,
   `LocaleSynchronization`, wagtail-localize's translation rows (after the
   copy is verified), `en` Locale.
6. **Flip** `WAGTAIL_I18N_ENABLED = False`.

Dry-run report lists: fallback-copied pages, pages whose structure differs
from nb, language-specific images/links (lost), references to repoint,
English addresses that will change.

**Prod data survey (2026-10-12, prod copy):** 261 en pages (85 aliases),
1,096 wagtail-localize English strings (1,080 machine, 16 manual), 5
snippet translation sources (4 of them written in English first and
translated to nb: copied the other way round), English menu groups typed
straight into en copies (fallback pairing), 0 segment overrides, and 2
stray references (nb header messages linking to en tool pages). **English-
only pages: deleted** (user decision): 4 union duplicates created Aug 18
(each has a Norwegian page with the same Peoply ID and the same text;
their /en/ addresses redirect to the twin's English address) and "Kar", an
empty never-published draft. Any other English-only page makes the dry
run list it.

## Rehearsal on a copy of the production database (required)

1. **Get the copy:** newest `.dump` via `scp` (see
   `docs/operations/backups_and_recovery.md`, "Copying backups outside
   NREC").
2. **Restore** into a scratch database in local Docker Postgres.
3. **Record "before":** every `/nb/` and `/en/` URL from the sitemap, with
   title and status.
4. **Dry run:** review the report; fix the command, never the data by hand.
5. **Real run + checks:**
   - no references to deleted pages
   - English count matches; human ones keep `source` and `translated_by`
   - no page has more missing English after than before (proves the
     Norwegian format/hash match)
   - every old URL works or redirects; most old English URLs work
     unchanged
   - English titles match
   - menus and messages look right
   - test suite passes
6. **Repeat from a fresh restore** if the command changed.
7. **Clean up:** real user data — keep local, never commit, delete after.

Deploy only after a clean final rehearsal, with a fresh backup right before.

## Order of work (one session, one branch, one commit per step)

| Step | What |
|---|---|
| 0 | **Done 2026-10-12** (see Step 0 results). Quick check: translated fields on one `ArticlePage` + one `MenuGroup` with its links; StreamField, rich text with several sentences, nested blocks, page links stay nb; reading `title` doesn't translate `body`; every read is caught; English never reaches the database; a re-fetched `.specific` is English; English slugs; wagtail-localize works with i18n off; list its admin buttons; measure the home page and an article list. |
| 1 | **Done 2026-10-12** (38 new tests, full suite 190 passing). Translation module (`page_segments`, `stored_translations`, `english_overlay`, `english_urls` storage functions), `SegmentTranslation` + `EnglishSlug` models, guard A, `translated_fields` on every model + rename protection, English preview mode. **Site works as today.** |
| 2 | **Done 2026-10-12** (23 new tests, full suite 213 passing; queue = timer + `WaitingForEnglish`, see Automatic translation). English editor (incl. slug), read-only superuser list, own DeepL client, auto-translate task + worker, setting. **Site works as today**; English rows fill in for the Norwegian pages. |
| 3 | **Done 2026-10-12** (212 tests passing; rehearsal below). **Switch-over**: migration command (dry + real, incl. English slugs), deletion, flip setting, middleware, slug routing + links (incl. redirects when an English slug changes), remove locale filters and `.localized`, switcher, sitemap, banner, hide wagtail-localize UI, nudges rewired, editor-mode link to the English editor (replacing the sync button), drop the `is_norwegian()` checks and `deepl.DeepLTranslator` adapter, seed data rewritten |

Why this order (changed 2026-10-12, when starting step 1): everything that
assumes "only Norwegian pages exist" must land together with the
migration that makes it true. Before that, the English page copies still
exist, so removing locale filters would list every page twice, and
English slug links need Wagtail's i18n off. Steps 1–2 leave the site
working as today.

The model attribute is called `translated_fields`, not
`translatable_fields`: wagtail-localize reads a `translatable_fields`
attribute itself and keeps syncing the two trees until the switch-over,
so reusing that name would break the current sync.
| 3b | **Done 2026-10-13** (see Step 3b results). Rehearsal on a copy of the production database |
| 4 | **Done 2026-10-13** (see Step 4 results). Remove dead code; docs (contributor doc `docs/architecture/shared/translations.md`, `docs/operations/prod_server.md` + management_commands.md for the two translate timers and `translate_english`, claude_context notes, `to_fix.md`) |

### Step 3 rehearsal results (2026-10-12, prod copy)

- `switch_to_english_overlay --apply`: 11 s; 794 wagtail-localize pieces
  + 15 English-first + 17 typed menu pieces copied; 763 pieces shown in
  English before -> 763 stored after (of 1,341; 578 left for DeepL); 121
  English slugs kept; 2 references repointed; 5 redirects; 5 English-only
  pages deleted (as decided); 1 English-only menu link lost ("UIO
  Verktøy" in the English "Tools" menu).
- All 488 old addresses requested: 235/235 /nb/ work; /en/ 234 work, 5
  redirect correctly, **14 now 404 because their Norwegian page is
  unpublished** while the English copy was still live (the "unpublish only
  hits nb" bug): 7 company presentations, 3 articles (incl. "Om
  IfiPlattform"), 2 tools, 2 categories ("Fadderuka", "Arrangementer").
  Their English addresses are unchanged, so republishing in Norwegian
  brings them back. Editors decide which should be public.
- English titles match (17 "mismatches" were HTML-escaped apostrophes, plus
  the 2 duplicates redirecting to their twins).
- Crawl of the switched site: 241 pages per language, 0 broken links, 0
  `href="None"`, 0 English pages linking into /nb/.
- Found while testing: dev and prod share one DeepL account, and
  `sync_deepl_glossary` deletes/recreates the glossary by name, so running
  it anywhere breaks the others' `DEEPL_GLOSSARY_ID` (local was already
  stale). Errors now say so.

Added in step 3 at the user's request (editors had them before):
"Machine-translate subtree" (page header/more menu and the English
editor; queued, works with auto-translate off), "Machine-translate menu"
(Menu snippet rows; groups + links in one DeepL batch), and links from the
English editor back to the Norwegian object and to the English page.

### Step 3b results (2026-10-13, fresh prod copy, final code)

Same dump as step 3 (content up to 2026-10-08), freshly restored. Steps
as in deploy.sh: `migrate` (0155-0159, 16 s), `switch_to_english_overlay`
dry run, then `--apply` (11 s, report identical to step 3); a second
`--apply` does nothing. "Before" crawled on main's code.

- Old addresses: same result as step 3 (235/235 /nb/, 234 /en/ unchanged,
  5 redirect, the same 14 404s). Titles match on every unchanged address.
- Crawl of the switched site: 470 sitemap URLs, 482 pages, 0 errors, 0
  `href="None"`, 0 English pages linking into /nb/. `/nb/` home text
  identical before and after.
- No references to the 260 deleted pages (text/JSON, foreign keys,
  reference index). The 10 human pieces keep `translated_by`. 0 error rows.
- `translate_english --nightly` (DeepL off): cleanup removed 59 unused
  rows (older Norwegian versions); still 763 of 1,341 pieces in English.
- Speed: same or faster (fewer queries); `/en/events/` 74 -> 134 ms.
- Full suite on Wagtail 7.4.3: 223 passing.
- English "Tools" menu had drifted from Norwegian; it now shows the
  Norwegian links (Peoply, IFI Rom, Grade Web). Lost from English: UIO
  Tools, Ifi Tools, Student ID+ (the report names only the first).
- Old code returns 500 on every page between `migrate` (0159 renames
  `menugrouplink.prefix`) and the gunicorn restart, about 30 s.

### Step 4 results (2026-10-13)

- Deleted: `translation/sync.py`, `snippets.py`, `views.py`, the
  `machine_translate_subtree`, `link_menu_translations` and
  `sync_translated_page_fields` commands (+ test, confirm template), the
  `DeepLTranslator` adapter and `WAGTAILLOCALIZE_MACHINE_TRANSLATOR`,
  `sync_mirrored_page` (view, URL, JS), `publish_target`,
  `SOURCE_LANGUAGE_CODE`, `style_target`, the en-copy publish/unpublish in
  `article_views`, `sync_locale_trees` and the `translation_key` dedup in
  the Peoply sync, `apply_peoply_match`'s multi-copy write and the admin's
  multi-copy event delete.
- `LEGACY_IMPORTERS` held only `switch_to_english_overlay`. After prod was
  switched, the command, its test, its deploy.sh line, `import_rows` and
  `is_translated_place` were deleted and `LEGACY_IMPORTERS` removed.
- Kept on purpose: `translation_key` on the style tables and as the
  Peoply union-mismatch identifier (one page per key now; re-keying needs a
  data migration). `test_force_sync_view.py` tests the Peoply "Sync now"
  button, not the two-tree sync, so it stays.
- Found and fixed: moving a page (or changing a Norwegian slug) made no
  English redirect, and with the admin in English Wagtail's own redirect
  handler saw no change under our `get_url_parts` and its empty batch
  **deleted every automatically created redirect**. Wagtail's
  `create_redirects` now always runs in Norwegian, and our own handlers add
  the English redirects (`english_urls.py`; tests in
  `AddressChangeRedirectTests`).
- No `cleanup_segment_translations` command exists: cleanup runs in
  `translate_english --nightly` only.
- Full suite: 212 passing.
- Added afterwards (same day): the two planned tests that were missing,
  golden format (`tests/test_segment_format.py` + `golden_segments.json`)
  and the fake-English crawl (`tests/test_english_crawl.py`, checked to
  fail when menu English is removed). Also: seed has complete English,
  `MenuGroupLink.prefix` -> `label_prefix` (0159, mapped in the switch-over),
  Wagtail 7.4.3. Suite: 223 passing.

### Step 0 results (2026-10-12)

Throwaway spike (`tests/test_step0_spike.py`, deleted after): 17 of 17
checks passed.

- **Works:** plain fields, rich text with several paragraphs (page links
  kept), nested blocks inside columns, menu groups and links, per-field
  translation, `.specific`, `get_children()`; a real GET of
  `/en/freshers-week/` rendered the article template in English with
  `WAGTAIL_I18N_ENABLED = False`, `/nb/fadderuke/` stayed Norwegian;
  English slug links and routing; wagtail-localize extraction and
  `manage.py check` with i18n off.
- **Found and fixed in the plan (guard A):**
  - an unguarded `save()` while English is on stores English
  - `refresh_from_db()` / deferred loading while English is on copies
    English into the object's Norwegian values (invisible on screen)
  - `get_children()` and breadcrumbs return plain `Page`, so Wagtail's
    `Page` needs the translated `title` too
  - the write blocker refused all five write paths tried; reads, other
    tables and a full English request were unaffected
- **Speed** (prod copy, overlay with one lookup query per object):

  | Page | Queries without → with | Objects looked up | Time |
  |---|---|---|---|
  | Home `/nb/` | 279 → 378 | 99 | no measurable difference (~1.2 s locally, DEBUG) |
  | Article list `/nb/infoartikkler/praktisk/` | 76 → 94 | 18 | no measurable difference (~0.1 s) |

  `prefetch()` stays in Later phases. The home page's 279 queries
  without the overlay are a separate, existing problem (being fixed on
  its own).
- **wagtail-localize admin hooks to hide in step 2**
  (`wagtail_localize/wagtail_hooks.py`): `register_admin_urls`,
  `register_permissions`, page listing "more" buttons,
  `register_snippet_listing_buttons`, `before_edit_page`,
  `before_edit_snippet`, two page action menu items (restart translation,
  convert back to alias), snippet action menu item,
  `register_reports_menu_item`.

## Later phases

Nothing here changes the database shape, so each can be added without a
rebuild.

- **Suggestions in the English editor:** when the Norwegian changed,
  show the previous human fix next to the new DeepL text; notice "the
  Norwegian changed while you were editing". (The old rows are already
  kept by cleanup.)
- **Choice when auto-translate is switched back on:** "Translate missing
  text now" or "Wait for the nightly job".
- **Worker health on the settings page:** last successful translation run
  and number of failed jobs.
- **`prefetch(pages)`:** load translations for a whole list in one query,
  only if pages turn out slow (step 0 measures).
- **Consider: a cache for English pages.** Not in this build, because
  stale-text bugs are the main risk of caching. Step 0 measures speed. If
  ever needed: use a new random version token on every change, so a lost
  cache key means a rebuild, never old text.

- **Remove wagtail-localize completely** (optional, whenever it's worth
  it, e.g. if it lags behind a Wagtail upgrade): rewrite the extraction in
  `page_segments.py` with our own code (walk StreamField blocks, split
  rich text). Done when the golden format tests pass. No data migration,
  nothing else changes. Then uninstall it and drop its tables.
- **Machine-translated / reviewed notices:**
  - two public notices on English pages: "machine-translated" and
    "machine-translated and reviewed by a person"
  - "English reviewed" checkbox in the admin, with who/when
  - new DeepL translation unchecks it; human fixes don't
  - menus and messages get the same checkbox, shown only in the admin
- **Full translation history:** author + editors instead of
  `translated_by`.

## Trade-offs (accepted)

| Trade-off | How it's handled |
|---|---|
| Field values depend on language ("magic": `page.title` is English on `/en/`) | the same model as `django-modeltranslation`; contributor doc; tests |
| English must never reach the database | guard A: writes to translated tables refused while English is on; Norwegian on re-reads; English only on GET/HEAD display and previews; tests |
| Patches Wagtail's own `Page` class (`title`, `seo_title`, `search_description`, `refresh_from_db`) | installed in one place at startup; tests fail with fix instructions on a Wagtail upgrade that changes it |
| One small query per page shown | per-field translation + per-request memory; `prefetch()` later if step 0 shows it's needed |
| Code bypassing model fields (e.g. `.values("title")`) shows Norwegian | rare; the fake-English crawl test is the safety net |
| Every page exists in both languages | accepted (no per-page opt-out) |
| Images and links shared | images with text noted in `to_fix.md`; dry run lists lost overrides |
| A few English addresses change once (clashes, differing trees) | redirects; listed in the dry-run report |
| Relies on wagtail-localize internals | only in `page_segments.py` (a test blocks imports elsewhere); pinned version; golden format tests; stored data, hash and DeepL client are ours, so it can be replaced without touching data |
| English routing is our own code (`route()` / `get_url_parts()`) | one file, `english_urls.py`; tests per page type |
| Own table instead of theirs | data copied in migration; ~50 lines more code |
| Only last translator kept | full history later |
| Own code to maintain (editor, worker, module) | net code still goes down |
| Not standard Wagtail | contributor doc |
| Two new systemd timers (`translate_english` every minute + nightly) | operations doc; pages still show if they stop |
| Renaming a field orphans its translations | snapshot test blocks the PR and says how to fix; `rename_segment_path` helper |
| Rollback = restore backup | rehearsal first |
| Search (none today) needs an English index if added | noted in `to_fix.md` |

## Code removed

- **Sync:** `translation/sync.py`, `page_published` receiver,
  `sync_translated_page_fields`, `link_menu_translations`,
  `translation/snippets.py`, `sync_locale_trees` call in Peoply sync
- **Admin hiding:** `admin_locales.py` (filters,
  `NorwegianFirstSnippetViewSet`, superuser toggle),
  `wagtail_localize.locales` app
- **Editor-mode workarounds:** `publish_target`,
  `can_sync_mirrored_page`, `sync_mirrored_page` view + button JS,
  double publish/unpublish (`views/article_views.py:509-597`)
- **Locale workarounds:** `translation_key` dedup in `event/pages.py`,
  `event/queries.py`, `sync_peoply_events.py`; multi-copy write in
  `apply_peoply_match`; alias branches in `status.py` / `page_mixins.py`
- **Seed:** `_translate_page`, `_sync_english_locale`, `fix_tree` (seed
  writes `SegmentTranslation` rows instead)
- **Lookups of the other copy:** `.localized` calls, `locale=Locale.get_active()`
  filters, `site_tags.translated_page_url` ancestor walk
- **Tests:** `test_admin_locales.py`, `test_force_sync_view.py`
- Kept but rewired: nudges (`nudge.py`, `status.py`) read
  `translation_status()`

## Tests

| Area | Checks |
|---|---|
| Translated fields | translated / missing / outdated after nb edit / fix survives unrelated edit / glossary / rich text with several sentences / reading `title` doesn't translate `body` / `.specific` and `get_children()` give English / menu link labels English / English admin UI still shows Norwegian |
| Database guard | while English is on: `save()`, `save_revision()`, `update()`, `bulk_update()` and snippet saves are refused; reads and untranslated tables work; `refresh_from_db()` and deferred loading keep Norwegian values; plain `Page` titles are English; POST/AJAX under `/en/` sees Norwegian; `english_active()` cleared between requests, also after an error; StreamField reads are caught too |
| Storage | DeepL insert never overwrites a human row; our `segment_hash` matches wagtail-localize's; a fix saved after the Norwegian changed attaches to the old text |
| Golden format | fixed example pages → exact expected pieces, paths and hashes (any future extractor must pass) |
| Isolation | no project file except `page_segments.py` imports `wagtail_localize` |
| English slugs | set from first English title; unchanged when title changes; editor change → redirect; clash → `-2`; no English slug → Norwegian slug works; Norwegian slug under `/en/` redirects to English one; move → redirect; links on a card list cost one slug query total |
| Cleanup | deleted page and block rows removed; old `deepl` removed; newest old `human` kept; drafts delete nothing; deleted user keeps rows |
| Translatable fields | every model declares them; no IDs, colours or slug extracted |
| Rename protection | renaming/removing a translatable field fails the snapshot test with the fix instructions; `rename_segment_path` moves stored English |
| Adapter | pins wagtail-localize behaviour |
| Crawl (safety net) | fake English everywhere → no Norwegian title or menu label on any `/en/` page |
| Banner | the one rule, incl. worker down → shown after 10 min |
| Setting | off → nothing queued; manual works; non-superuser can't edit |
| Pages | `/en/` English per page type; `/nb/` unchanged; drafts 404; DRAFT banner both; menus/home in English |
| wagtail-localize UI | its buttons are gone |
| Rehearsal | all checks pass on a clean run |

Full test suite runs (model and migration work).
