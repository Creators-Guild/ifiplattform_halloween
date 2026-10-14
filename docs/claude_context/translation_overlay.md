# English overlay (translation/*.py, models/translation.py) — design notes

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/translation/page_segments.py, ifiplatform/apps/ifi_home_app/translation/stored_translations.py, ifiplatform/apps/ifi_home_app/translation/english_overlay.py, ifiplatform/apps/ifi_home_app/translation/english_urls.py, ifiplatform/apps/ifi_home_app/translation/auto_translate.py, ifiplatform/apps/ifi_home_app/translation/deepl.py, ifiplatform/apps/ifi_home_app/translation/english_editor.py, ifiplatform/apps/ifi_home_app/models/translation.py, ifiplatform/apps/ifi_home_app/management/commands/update_translation_snapshot.py, ifiplatform/apps/ifi_home_app/management/commands/translate_english.py

Context for future Claude sessions. Not a human-facing doc. The plan and
its decisions: `docs/claude_plans/translation_redesign.md`.

## Status

Done and in production (plan: `docs/claude_plans/translation_redesign.md`):
`WAGTAIL_I18N_ENABLED = False`, one Norwegian tree, English shown under
/en/ by `EnglishDisplayMiddleware`. Only `page_segments.py` imports
wagtail-localize (test_translated_fields_guard). `translation_key` stays on the style
tables (`ArticleStyle`, `ArticleBlockStyle`, `PageBannerStyle`) and as
the identifier of Peoply union mismatches: one page per key now, so it's
harmless and re-keying would need a data migration.

## Model attribute: `translated_fields`, not `translatable_fields`

wagtail-localize reads a `translatable_fields` attribute itself (expects
TranslatableField objects) and keeps syncing the two trees until the
switch-over. Reusing that name would break it. Every page type and
translatable snippet declares `translated_fields` explicitly (test fails
otherwise). Wagtail's own `title`, `seo_title`, `search_description` are
added for every page by `page_segments.translated_field_names()`; page
types don't list them. `untranslated_block_paths` (stored-path form,
`sitting_members.*.name`) keeps text blocks out, e.g. people's names.
`check_translated_field()` (run by `install()` at startup) rejects choice,
URL, email, slug and non-text fields.

## english_overlay.py

- `TranslatedField` must be a **data descriptor** (get + set): Django puts
  loaded values in `obj.__dict__`, which skips a get-only descriptor. It
  wraps the original attribute (Django's `DeferredAttribute`, or Wagtail's
  StreamField `Creator`), which keeps holding the Norwegian value; `__set__`
  delegates to it and drops the per-object memo (`_english_values`).
- Installed on the **owner** class of each field (`field.model`), so
  `title` goes on Wagtail's `Page`: `get_children()`, breadcrumbs and
  `get_parent()` return plain `Page` objects (found in step 0).
- `english_active()`: `_english` ContextVar and not `_raw`. ContextVars,
  not thread-locals, so async is correct too; always reset with the token
  in `finally`.
- **Copy-back methods** (`refresh_from_db`, `full_clean`, `clean_fields`)
  are wrapped in `raw_norwegian()` on every owner. They do
  `setattr(obj, name, f(getattr(obj, name)))`; with English on that put
  English into the Norwegian slot (step 0 for refresh/deferred loading;
  `full_clean` found in step 1 via `save()`, which calls it first). The
  object then *looks* right, and a later save stores English.
- **Write blocker** (`block_english_writes`): an `execute_wrapper` added to
  every connection (`connection_created` + already-open ones). While
  `english_active()`, INSERT/UPDATE matching a translated table (owners'
  tables + `wagtailcore_revision`, word-boundary regex) raises
  `EnglishWriteBlocked`. Deliberately strict: display and previews never
  save, so it only fires on a bug. Raw-mode saves pass (they read
  Norwegian). Don't "fix" a block by wrapping `save()` in raw mode: that
  would hide the bug and weaken the last safety net.
- `_english_value()` never raises: on any error it logs and shows the
  Norwegian field (a page must never crash because of a translation).
  Writes can't record the error during display (blocked); bad English is
  caught when it's saved (`page_segments.check_english()`).
- `EnglishPreviewMixin.serve_preview()` renders the response **inside**
  `english()`: `TemplateResponse` renders lazily, after the block would
  have ended.

## page_segments.py (the only wagtail-localize importer)

- Stored text = wagtail-localize's `StringValue.data` (escaped, links as
  `<a id="a1">`); hash = `uuid5(HASH_NAMESPACE, text)` with their String
  namespace copied in as our constant. Migrated rows match only because of
  this; a test pins it. Never change either. `tests/test_segment_format.py`
  + `golden_segments.json` pin whole objects' pieces (paths, texts,
  hashes) with fixed block ids: the check for a wagtail-localize upgrade or
  replacement. Never regenerate the JSON to make it pass.
- `tests/test_english_crawl.py` (slow): fake English (`EN·` + Norwegian)
  for every piece of the seeded site, crawl /en/, fail on any text node
  that is exactly a Norwegian plain-text piece. Catches code that reads
  around the fields.
- Related-object segments (page/image choosers) are dropped: links and
  images stay Norwegian. Override segments (hrefs) are kept so rich text
  reassembles.
- Every segment value gets a sequential `order`: wagtail-localize's writer
  sorts by it (`organise_template_segments`) and `None` can't be sorted.
- `apply_translations()` writes into `field.to_python(value.get_prep_value())`,
  a fresh copy with the same block ids: wagtail-localize's writer edits in
  place. Cost: chooser blocks load again on the copy (a few queries).
- ListBlocks in the old pre-2.16 format (no item ids) give no pieces
  (wagtail-localize behaviour).

## stored_translations.py

- Rows keyed by the page's **specific** content type + id, so a plain
  `Page` and its `.specific` share rows. Snippets: `get_for_model`.
- `lookup()` memo lives in `obj.__dict__["_english_rows"]`; Wagtail's
  `.specific` copies `__dict__` entries, which is fine (same rows).
- `save_machine()` is `bulk_create(ignore_conflicts=True)`: DeepL never
  overwrites a row, so a person's fix always wins whatever the order.
- `cleanup()` counts the stored object **and** the latest draft as
  current, so drafts never delete rows (also not draft-only pieces an
  editor translated early).
- `rename_segment_path()` takes the historical `apps` so migrations can
  use it.

## english_urls.py

- `request_scope()` memo (ContextVar): all English slugs and the whole page
  tree (`path` → id, slug) once per request, so building many links costs
  no queries. Outside a scope every call queries.
- English slugs must also differ from siblings' **Norwegian** slugs: a page
  without an English slug uses its Norwegian slug under /en/.
- Hooked into `route()`/`get_url_parts()` only at the switch-over (needs
  `WAGTAIL_I18N_ENABLED = False`).

## Rename protection

`translation/translated_fields.json` maps every model's readable place
("body → image → caption") to its stored-path form ("body.*.caption").
`RenameProtectionTests` fails on any difference and prints the
`rename_segment_path(...)` line to put in the migration. Readable form
names block types so struct-field renames are caught even where two block
types share a field name; a block **type** rename keeps the stored form and
moves nothing (the message says so). `manage.py update_translation_snapshot`
rewrites the file.

## auto_translate.py (DeepL in the background)

- **Timer + table, not a task queue** (decided in step 2): django-tasks
  0.12's database backend moved to a separate 0.x package. Publishing a page
  (`page_published` signal: editor, scheduled, workflows, commands; never
  draft saves) or saving a translated snippet (`post_save`, skipped for
  `raw`) upserts a `WaitingForEnglish` row. `manage.py translate_english`
  runs every minute (`deploy/systemd/ifiplatform-translate.timer`; a run
  still busy isn't started twice) and `--nightly` at 03:30.
- `translate_waiting()` locks each row with `select_for_update(skip_locked)`
  while translating, so an overlapping nightly run skips it, and a publish
  during the DeepL call waits and then inserts a fresh row (translated next
  minute) instead of being lost. `fill_missing()` runs in a savepoint, so a
  DB error still lets the failure be recorded on the row.
- Failures: `attempts`, `last_error`, retried after 2, 4, 8 … 60 minutes.
  Unpublished pages and deleted objects drop their row.
- DeepL output that fails `check_english()` is stored with `has_error`
  (shows as missing), and `drop_failed_machine_rows()` deletes those before
  the next try, because `save_machine()` is insert-only.
- English slug: set once from the first English title
  (`set_english_slug_if_missing`), never from later title changes.
- Nightly: `forget_stale_glossary_rows()` (DeepL rows with a glossary term,
  older than `GlossarySyncState`), mark everything whose
  `translation_status()` has missing or errors, translate, then
  `cleanup()` (cleanup also runs with auto-translate off).
- No DeepL key (`settings.DEEPL_API_KEY`): nothing is marked and nothing is
  sent; tests patch `deepl.translate_texts`.
- `fill_missing_many(objects)`: all missing pieces of several objects in
  as few DeepL requests as possible (50 texts each); `fill_missing` is the
  one-object case. Used for a menu group with its links and whole menus.
- `request_subtree(page)` ("Machine-translate subtree"): marks the page and
  its live descendants with `requested_by_person=True`; with automatic
  translation off, `translate_waiting()` only processes such rows. Queued,
  not done in the request: a big tree takes minutes.
- `deepl.translate_texts` raises an `HTTPError` with DeepL's own message
  plus a hint (404 with a glossary set = `DEEPL_GLOSSARY_ID` doesn't exist
  on that DeepL account; `sync_deepl_glossary` recreates glossaries under
  new IDs, so a stale ID is a realistic failure).

## english_editor.py

- Each form row carries its object, path and **the Norwegian the editor
  saw**; a fix is saved against that, never the text at save time (if the
  Norwegian changed meanwhile, the fix attaches to the old text and the new
  text gets DeepL). Rows refused by `check_english()` re-render with the
  error.
- A menu group's editor also lists its links (`get_all_child_relations`):
  each link is its own object in the tables.
- Header links: back to the Norwegian object (`AdminURLFinder` edit URL),
  "View in English" (live pages), and the subtree confirm view.
  `machine_translate_menu` (button on `Menu` snippet rows) DeepL-fills a
  whole menu (groups + links) synchronously in one batch.
- The English slug field must render "" for a page without one (a None
  rendered as "None" would be saved as the slug "none").
- `StoredEnglishViewSet`: the read-only superuser list
  (`SuperusersMayLookPolicy`: superusers may "view", nobody may add/change/
  delete). The only reader of SegmentTranslation besides
  stored_translations.py.

## Routing, links and the middleware (switch-over)

- `english_urls.install()` replaces Wagtail's `Page.route` and
  `Page.get_url_parts` (not a page mixin): breadcrumbs, child lists and
  plain `Page` links need English addresses too. Addresses follow the
  language prefix (`wants_english_address()`), not `english_active()`.
- `get_url_parts`: the original call (which, with i18n off, reverses with
  the active language's prefix) then the path rebuilt from English slugs;
  the site root's depth comes from its `root_path`. A page not in the tree
  yet (new page preview) keeps the original parts.
- `route`: English slug first, then Norwegian slug; a Norwegian slug
  under /en/ for a page that has an English slug raises
  `MovedToEnglishAddress`, which the middleware's `process_exception`
  turns into a 301.
- `EnglishDisplayMiddleware` (after LocaleMiddleware): `request_scope()`
  for every request, `english()` for GET/HEAD under /en/ outside
  `/wagtail-admin/` and `/admin/`. TemplateResponses render inside it.
- `set_english_slug()` creates Wagtail redirects (old -> new English
  address, page + live descendants) when a live page's English address
  changes, including the first DeepL slug replacing the Norwegian
  fallback. `redirect=False` is for fresh data (the seed).
- **Moves and Norwegian slug changes** (step 4): Wagtail's redirects app
  compares a page's old and new address, but under "en" our
  `get_url_parts` reads the tree as it is *now*, so both look equal; its
  empty batch then deletes **every** automatically created redirect
  (`BatchRedirectCreator.pre_process` filters on an empty `Q()`). Found when
  an admin running in English moved a page in a test. `install()` therefore
  replaces `wagtail.contrib.redirects.signal_handlers.create_redirects` with
  a wrapper that runs it in Norwegian (Wagtail's handlers look the name up
  at call time). English redirects come from our own `pre_page_move`/
  `post_page_move` handlers (addresses before/after) and `page_slug_changed`
  (only for pages without an English slug, whose /en/ address uses the
  Norwegian slug; old addresses derived by swapping the slug in the new
  prefix, since the signal fires after the save). `page_slug_changed` is
  sent on commit: tests need `captureOnCommitCallbacks`.
- Sitemap: Django's i18n sitemap (`i18n`, `languages`, `alternates`), one
  entry per page per language.

## The switch-over (done, command deleted)

Production was switched with `switch_to_english_overlay` (one-time;
deleted afterwards, see git history and the plan's rehearsal results). It
copied wagtail-localize's English into `SegmentTranslation`, kept English
slugs, repointed references and deleted the English tree. Migration 0157
deletes an *unused* "en" locale on fresh databases.

## status.py and nudges

Rewired onto these tables: see `translation_nudge.md`. Tests force
`DEEPL_API_KEY = ""` (settings.py), whatever .env says.

## deepl.py (our DeepL client)

- `translate_texts()` sends the same request wagtail-localize's
  DeepLTranslator did (NB -> EN, `tag_handling=xml`, glossary), in batches
  of 50, and checks the HTTP status first. History: wagtail-localize's
  client called `response.json()` without `raise_for_status()`, so a rate
  limit or quota answer showed up as an opaque `JSONDecodeError` (seen on a
  164-page bulk translation). `DEEPL_CALL_DELAY_SECONDS` paces
  `translate_waiting()` between objects for the same reason.
- No wagtail-localize machine translator is configured any more
  (`WAGTAILLOCALIZE_MACHINE_TRANSLATOR` removed in step 4); its admin UI is
  hidden.
- Glossary: `sync_deepl_glossary` deletes and recreates the glossary by
  name (DeepL glossaries can't be edited) and records `GlossarySyncState`.
  Dev and prod share one DeepL account, so running it anywhere invalidates
  the others' `DEEPL_GLOSSARY_ID`. The nightly run redoes DeepL rows that
  contain a glossary term and predate the sync
  (`stored_translations.forget_stale_glossary_rows`, case-insensitive like
  DeepL's own matching); human rows are never touched.

## Wagtail upgrades (checked 2026-10-13 against 8.0)

Staying on LTS (7.4.x; next 8.3). What a major upgrade must re-check,
since this module patches Wagtail internals:
- `Page.route` / `Page.get_url_parts` replaced in `english_urls.install()`
  (8.0: same signatures; `_get_relevant_site_root_paths(cache_object)`
  unchanged).
- `wagtail.contrib.redirects.signal_handlers.create_redirects` replaced
  (8.0: still a module global looked up by the handlers).
- Translated-field descriptors on Wagtail's `Page` (8.0: `Page` =
  `AbstractPage` + `DefaultBasePageMixin`, swappable via
  `WAGTAIL_PAGE_MODEL`; fields still concrete on `Page`).
- 8.0 wants custom viewset policies registered:
  `register_permission_policy(SegmentTranslation, SuperusersMayLookPolicy(...))`
  for `english_editor.StoredEnglishViewSet` (otherwise a deprecation
  warning).
- wagtail-localize must support the target (1.14.5 supports 8.x); only
  `page_segments.py` uses it.
