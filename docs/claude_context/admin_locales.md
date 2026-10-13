# Norwegian-only admin (`ifi_home_app/translation/admin_locales.py`)

Last updated: 2026-09-24
Covers: ifiplatform/apps/ifi_home_app/translation/admin_locales.py, ifiplatform/ifiplatform_project/settings.py

Norwegian (nb) is the content source of truth. English (en) is mirrored from
it through wagtail-localize: the `LocaleSynchronization` row (en syncs from
nb), the translation editor, and the `page_published` sync hook. Editors
should therefore only see and work in Norwegian.

## How

- **`LANGUAGE_CODE = "nb"`** makes nb Wagtail's default locale.
  `Locale.get_default()` is what every admin listing falls back to without
  `?locale=` (`wagtail/admin/views/generic/mixins.py`), so snippet
  listings, "Add snippet" and new root pages open in nb. Two side effects:
  - A visitor with no language preference lands on `/nb/`.
  - Anything translated outside a request (management commands, tests)
    renders in Norwegian. Pin tests with `translation.override("en")`
    where English is expected. `/en/` itself is unaffected: Django never
    falls back from an English catalog to the default language.
- **`construct_explorer_page_queryset`** (`filter_explorer_pages`) keeps
  only pages in the parent page's locale, or nb at the tree root. One hook
  covers the explorer listing, explorer search and the sidebar explorer.
  - Filtering by the parent's locale, rather than always by nb, is
    deliberate. An English page reached through its nb page's
    "Translations" menu still lists its English children, so mirroring
    stays usable.
- **`construct_page_chooser_queryset`** (`filter_chooser_pages`) is nb only.
  Page links, e.g. in menu groups, are stored against nb pages and
  resolved with `.localized` when rendered.
- **Snippets** have no queryset hook, and Wagtail's snippet listing and
  chooser default their locale filter to "All", ignoring
  `LANGUAGE_CODE`. The translatable snippets (`HeaderMessage`,
  `HomeBoardMessage`, `MenuGroup`) are therefore registered in
  `wagtail_hooks.py` with `NorwegianFirstSnippetViewSet` instead of
  `@register_snippet`. It preselects `locale=nb` whenever no locale was
  requested, for both the listing (and its AJAX results) and the chooser.
  Picking "English" or "All" in the filter still works. Any new
  translatable snippet should be registered the same way.

## Superuser toggle

A sidebar item ("Show/Hide English pages", superusers only) hits
`toggle-all-locales/`, which flips `request.session["show_all_locales"]`.
- Default is off, so English is hidden for everyone.
- The flag lasts for that login session.
- Non-superusers are ignored even if the flag somehow gets set.
