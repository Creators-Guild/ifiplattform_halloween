# management/seed_dev_data/ — design notes

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/management/seed_dev_data/events.py, ifiplatform/apps/ifi_home_app/management/seed_dev_data/helpers.py, ifiplatform/apps/ifi_home_app/management/seed_dev_data/users.py

Context for future Claude sessions. Not a human-facing doc.

## events.py — ordering gotchas (don't reorder these without reading this)

- Fadderuke's sub-events (`FADDERUKE_SUB_EVENT_SPECS`) are a Mon-Fri
  programme, so Fadderuke itself always starts on the *next Monday* rather
  than `EVENT_SPECS`'s plain day offset — otherwise its week would land on
  arbitrary weekdays depending on when the command runs.
- Fadderstyret hosts the whole week, not just one sub-event — set directly
  on Fadderuke itself so `EventPage.all_related_unions` has a real "host"
  at the top level (every other union only hosts one sub-event, which
  `all_related_unions` caps down to "collaborator" once rolled up).
- **`_translate_page(fadderuke, ...)` must run before any sub-event is
  translated, not after.** wagtail-localize's `Translation.save_target
  (copy_parent_pages=True)` auto-creates a bare, untranslated copy of a
  page's parent the moment a *child* gets translated and the parent has no
  translation yet. If that fired first, `has_translation(en_locale)` would
  already be `True` by the time `_translate_page(fadderuke, ...)` ran, and
  it would skip — silently leaving Fadderuke's own en translation as that
  untranslated auto-copy forever (`calendar_legend`/`related_unions`
  structurally present, but never actually translated).

## helpers.py — _translate_page's slug re-save

wagtail_localize doesn't translate slugs (excluded from PO segments), so
the target page keeps the nb slug by default — re-slugified from the
now-translated title instead. Must be a plain, unrestricted `.save()`:
`publish()` doesn't write the slug back to the live row at all, and
`save(update_fields=["slug"])` recomputes `url_path` in memory but then
drops it (not in `update_fields`), silently breaking descendant URLs.
