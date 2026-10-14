# management/seed_dev_data/ — design notes

Last updated: 2026-10-13
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

## helpers.py — _translate_page / _store_english

Since the English overlay switch-over the seed builds one Norwegian tree
and no English locale.
`_translate_page(obj)` stores English for every piece whose Norwegian is
a key in `constants.TRANSLATIONS` (matched raw and in stored form: pieces
are escaped, "Paint &amp; Sip", the table isn't), or is in
`SAME_IN_ENGLISH` (names, Lorem Ipsum, the already-English banner: stored
as their own English, like DeepL would), through
`stored_translations.save_machine()` (insert-only, so re-running keeps
existing English), and gives a page its English slug from its English
title (`redirect=False`: nothing to redirect on a fresh database).
`_store_english(obj, {field: English})` does the same for plain fields
whose English comes from the specs instead (menu groups and links; a
link's `description` is a name, stored as its own English). Navet's
company presentations get dated English slugs set in events.py, since
slugs from the English title alone would clash (-2, -3 ...).
`tests/test_seed_dev_data.py` fails, naming the text, when a seeded piece
has no English or a page no English slug. The
old wagtail-localize gotchas (translating Fadderuke before its
sub-events, re-saving slugs) no longer apply: order doesn't matter now.
