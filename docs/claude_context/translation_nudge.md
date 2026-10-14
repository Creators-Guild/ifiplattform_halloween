# Translation nudges (`translation/status.py`, `translation/nudge.py`)

Last updated: 2026-10-13
Covers: ifiplatform/apps/ifi_home_app/translation/nudge.py, ifiplatform/apps/ifi_home_app/translation/status.py

Context for future Claude sessions. Not a human-facing doc. Since the
switch-over (one Norwegian tree, English stored as pieces; see
`translation_overlay.md`), English is edited in the English editor, and
DeepL fills missing English by itself within a minute of publishing. These
nudges only matter when that didn't happen: DeepL failing or off, or
English that didn't fit. Each links to the English editor ("Open English
editor"), which has the "Machine-translate now" button; `machine_url` is
always None and kept only so callers/templates needn't change.

## Status rules (`translation_status(page, user)`)

From `english_overlay.translation_status()` piece counts:
- `None` for the tree root, while the page is waiting for DeepL (less than
  `auto_translate.PENDING_MINUTES`), or when nothing is missing/failed.
- **outdated**: some pieces lack English but the page has stored rows
  (it had English; Norwegian changed since).
- **missing**: no rows at all.

`page_needs_translation(page)` is the visitor banner ("not translated
yet", via `TranslationWarningMixin`): only while English is shown
(`english_active()`), some pieces missing or failed, and not waiting. That
is the plan's one banner rule.

## Where the nudges appear

- **After publishing / edit view**: a Wagtail warning message (edit view on
  GET only, so it doesn't pile up). Right after publishing the page is
  normally waiting for DeepL, so no message.
- **Dashboard**: `TranslationsNeededPanel` via `pages_needing_translation()`,
  under "How this site works" (30) and "Shortcuts" (40), both in
  `admin_dashboard.py`; this panel is 50.
  Always shown: "All English is up to date" when nothing is stuck.
  Lists only pages stuck waiting longer than `PENDING_MINUTES` or with
  `has_error` rows -- not a scan of every page, which took 1.5–2.5 s per
  dashboard load on prod data.
- **Explorer**: "Needs translation" listing button (status per row).
- **Frontend editor mode**: `EditorModeMixin.translation_nudge(user)`
  (editors only), rendered by `info_articles/partials/translation_nudge.html`
  on article, category, index and student-union category pages.
