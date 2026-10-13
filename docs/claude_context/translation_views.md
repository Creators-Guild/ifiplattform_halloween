# translation/views.py + machine_translate_subtree command — design notes

Last updated: 2026-09-24
Covers: ifiplatform/apps/ifi_home_app/management/commands/machine_translate_subtree.py, ifiplatform/apps/ifi_home_app/translation/deepl.py, ifiplatform/apps/ifi_home_app/translation/views.py

Context for future Claude sessions. Not a human-facing doc. The actual
translate-and-publish work lives in the `machine_translate_subtree`
management command (`ifi_home_app/management/commands/`); `views.py` only
validates the request and launches it as a background process -- see below
for why.

## machine_translate_subtree

Unlike wagtail-localize's own "Translate" button (creates empty
translations, one page/subtree at a time, no content) and "Machine
Translate" button (fills in DeepL content, but only for whichever single
page's translation editor is open), this walks `page` and every
descendant, creates/updates each one's English translation, fills it in
via DeepL, and publishes it — all from one confirm screen. Registered as a
wagtail-admin URL (`wagtail_hooks.py`'s `register_admin_urls`) rather than
under `ifi_home_app/urls.py`, so it inherits wagtail-admin's own
login/session handling the same way wagtail-localize's own views do.

`machine_translate_page` is the single-page variant: the same view logic,
confirm screen and background launch with `page_only=True`, running the
command with `--page-only`. It's the "Machine-translate now" button of the
translation nudges (see `translation_nudge.md`).

### Runs as a background process, not inline

Originally ran the whole translate-and-publish loop synchronously inside
the request. Broke for real on a 164-page subtree: one DeepL call per page,
all wrapped in one `@transaction.atomic` block, took well over gunicorn's
default 30s worker timeout -- the worker got killed mid-translation
(`[CRITICAL] WORKER TIMEOUT`) after ~25 minutes and only 42/164 pages done.
Raising the timeout just moved the failure later: with more time, the next
run hit `requests.exceptions.JSONDecodeError` from `wagtail_localize`'s own
`deepl.py`, which calls `response.json()` with no `raise_for_status()`
first -- 164 DeepL calls fired back-to-back with no delay between them very
likely tripped DeepL's own rate limiting, and that missing guard turned the
resulting error response into an opaque JSON decode failure instead of a
diagnosable one.

Fixed three ways at once, moving the real work to the
`machine_translate_subtree` management command:

- **Detached background process**, launched via `subprocess.Popen(...,
  start_new_session=True)` from the view, which now only validates the
  request and returns immediately with a "started" message. A plain
  background thread was considered and rejected -- it would die the moment
  the gunicorn worker running it gets recycled or the service restarts
  (e.g. the next deploy), silently losing all in-progress work. `systemd-cat
  -t machine-translate-subtree` wraps the actual command so its output
  lands in the journal (`journalctl -t machine-translate-subtree`) instead
  of `journalctl -u gunicorn`, since it's no longer a gunicorn child at all.
  `systemd-cat` doesn't exist on local dev (Windows) -- the view falls back
  to plain inheritance there (progress shows in the runserver terminal)
  rather than crashing on a missing binary.
- **A small delay between DeepL calls** (`DEEPL_CALL_DELAY_SECONDS` in the
  command) so requests aren't fired at DeepL back-to-back -- the direct fix
  for the rate-limit-shaped failure.
- **`ifi_home_app.translation.deepl.DeepLTranslator`** subclasses
  wagtail_localize's own `DeepLTranslator` to add the missing
  `raise_for_status()` (same pattern as
  `core_app.storage.LenientManifestStaticFilesStorage` subclassing
  `ManifestStaticFilesStorage` -- extend the third-party class rather than
  patch/vendor it). Wired in via `WAGTAILLOCALIZE_MACHINE_TRANSLATOR["CLASS"]`
  in `settings.py`. Now a bad DeepL response surfaces as a real, readable
  `HTTPError` in the per-page failure log instead of a bare JSON decode
  error.

**Resumable by construction, not by any added retry logic.**
`apply_machine_translation()` already skips any segment with an existing
`StringTranslation`, and each page's DeepL call covers that whole page's
untranslated segments in one request -- so a page is all-or-nothing at the
DeepL-call level (every segment gets a `StringTranslation` together, or,
now that failures raise cleanly, none do). The command also gives each
page its own `transaction.atomic()` block instead of one covering the
whole batch, and catches any per-page exception to log it and continue
rather than aborting the run. Put together: a re-run after a partial
failure costs zero extra DeepL calls for pages that already succeeded, and
only retries what failed or was never reached. "Just run it again" is the
entire recovery story -- verified directly (not just assumed) by forcing a
mid-batch failure and confirming a subsequent run only touches the
previously-failed pages.

## _clear_stale_glossary_translations

Lives in the `machine_translate_subtree` command now (moved with the rest
of the real implementation, see above) -- `apply_machine_translation()` skips any segment that already has a
`StringTranslation` — normally right, since an unchanged nb sentence keeps
its existing machine translation instead of burning DeepL quota
re-translating something that would come back identical (segments are
content-addressed by wagtail-localize). The one case that's wrong for: a
sentence containing a glossary term, translated *before* the glossary last
changed — DeepL would now translate it differently. This deletes just
those specific, still-stale, machine-made translations so
`apply_machine_translation()` redoes them; any human-corrected translation
is left untouched regardless of glossary terms.

Case-insensitive matching to match DeepL's own glossary matching (confirmed
empirically: `"Fadderuke"`/`"fadderuke"`/`"FADDERUKE"` in source text all
get matched and normalized to the glossary's defined casing).
