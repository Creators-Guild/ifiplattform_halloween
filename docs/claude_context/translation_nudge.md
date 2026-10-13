# Translation nudges (`translation/status.py`, `translation/nudge.py`)

Last updated: 2026-09-24
Covers: ifiplatform/apps/ifi_home_app/translation/nudge.py, ifiplatform/apps/ifi_home_app/translation/status.py, ifiplatform/apps/ifi_home_app/translation/views.py

English is hidden from editors in the admin (see `admin_locales.md`), so
nothing would otherwise remind them that an English copy needs work. These
nudges make it obvious, and each one offers two actions:
- **Machine-translate now**: the single-page variant of the subtree job
  (`machine_translate_page` view, `machine_translate_subtree --page-only`).
  It fills in missing text with DeepL in the background and publishes.
  Shown only when a machine translator is configured and the user has
  `wagtail_localize.submit_translation`.
- **Open translation editor**: for a missing copy, wagtail-localize's
  "Translate this page" form (`submit_page_translation`). For an out-of-date
  copy, the en page's edit URL, which wagtail-localize's `before_edit_page`
  hook turns into the translation editor. Direct URLs still work even
  though the explorer hides English.

## Status rules (`translation_status(nb_page, user)`)

Status is always computed from the nb page:
- **missing**: there is no en copy, or it is still an alias (the
  placeholder locale sync creates, which shows nb content).
- **outdated**: the en copy's wagtail-localize `Translation` has fewer
  translated segments than its source (`get_progress()`). Every nb publish
  refreshes the source (`sync.py`, `update_from_db`), so new or changed nb
  text shows up here right away.
- Otherwise `None`. It is also `None` for non-nb pages and the tree root.

`page_needs_translation(en_page)` is the same check seen from the en side.
It drives the public "not translated yet" badge through
`TranslationWarningMixin`.

A cheaper "source newer than its translations" pre-check was considered
and rejected. It misses a translation that was only partly done after
the last source update. `get_progress()` is a single aggregate query
anyway.

## Where the nudges appear

- **After publishing**: `after_publish_page` adds a Wagtail warning
  message with both buttons. It shows on the page Wagtail redirects to.
- **Edit view**: `before_edit_page` adds the same message, on GET only so it
  doesn't pile up on save.
- **Dashboard**: `construct_homepage_panels` adds `TranslationsNeededPanel`.
  It lists the pages under a site root, most recently published first, up
  to 25 of them, with the total count. `pages_needing_translation()` fetches
  the en copies and Translations in bulk, so only the segment count runs
  per page. The panel is hidden when nothing needs translation.
- **Explorer**: `register_page_listing_buttons` adds a "Needs translation"
  button. These render inline next to the page title, so it doubles as a
  status tag. "Machine-translate now" is in the row's "more" menu and the
  page header.
- **Frontend editor mode**: `EditorModeMixin.translation_nudge(user)` puts
  the status of the nb copy into context as `translation_nudge`, so the
  banner also shows when viewing the en alias or translation. It is only
  set for users who can edit. `info_articles/partials/translation_nudge.html`
  renders the banner. It covers article, category, index and
  student-union category pages; the other page types have no editor mode.
