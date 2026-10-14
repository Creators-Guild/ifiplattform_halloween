# Translations

Last updated: 2026-10-13

How the site is shown in Norwegian and English: page content, menus and
messages (written by editors), and the fixed texts in templates and code
(written by developers). Read this before you add a field to a page type
or snippet, or rename one.

## In short

- There is **one page tree, in Norwegian**. There are no English pages.
- English is stored as **translated text pieces** next to the Norwegian
  pages. On `/en/`, reading a field such as `page.title` or `page.body`
  gives the English automatically. Normal code and templates need no
  special handling.
- **DeepL** fills in the English about a minute after a page is published
  or a snippet is saved. Editors can correct it, and a correction is kept
  until the Norwegian text under it changes.
- **English addresses** use English slugs (`/en/freshers-week/` for
  `/nb/fadderuke/`).
- Fixed texts in templates and Python code use Django's normal
  `{% trans %}` / `_()` and the `.po` files (see [the end](#fixed-texts-in-templates-and-code)).

## What a visitor gets

| Request | What happens |
| --- | --- |
| `GET /nb/fadderuke/` | The page, in Norwegian |
| `GET /en/freshers-week/` | The same page. Every translated field reads as English |
| `GET /en/fadderuke/` | Redirects to `/en/freshers-week/` (the Norwegian slug is found, the page has an English one) |
| A page with no English slug yet | Its Norwegian slug is used in the `/en/` address |
| A piece with no English yet | Shows in Norwegian. The page shows "This page hasn't been translated yet", unless DeepL is about to run (less than 10 minutes waiting) |

Publish status, drafts, styles and images are the same in both languages,
because there is only one page. Images and page links are never
translated.

## Where English is stored

All of this is in `apps/ifi_home_app/`.

| Table | One row per | Written by |
| --- | --- | --- |
| `SegmentTranslation` | piece of text: "at this place on this page, this Norwegian is this English" | DeepL (`source = deepl`) or a person in the English editor (`source = human`) |
| `EnglishSlug` | page with an English slug | DeepL (from the first English title) or a person in the English editor |
| `WaitingForEnglish` | page or snippet waiting for DeepL | publishing a page, saving a translated snippet |

A piece is matched on its place **and** the exact Norwegian text. When an
editor changes a Norwegian sentence, its old English no longer matches,
and DeepL translates the new one. That is why English can't drift out of
date unnoticed. DeepL never overwrites a row that already exists, so a
person's correction always wins.

Superusers can browse every row under **Stored English** in the Wagtail
admin (read only).

The code is in `translation/`:

| File | Job |
| --- | --- |
| `english_overlay.py` | Makes translated fields return English on `/en/`, and stops English from ever being saved into the Norwegian pages |
| `page_segments.py` | Splits a field into text pieces and puts English back in. The only file that uses wagtail-localize |
| `stored_translations.py` | The only code that reads or writes `SegmentTranslation` |
| `english_urls.py` | English slugs, `/en/` routing and links, and redirects when an address changes |
| `auto_translate.py`, `deepl.py` | Sending missing English to DeepL |
| `english_editor.py` | The English editor and the buttons in the Wagtail admin |
| `status.py`, `nudge.py` | "Missing" / "out of date" notices for editors |

## When DeepL runs

1. An editor publishes a page (in the admin, in Editor mode, by a
   schedule, or a command such as `sync_peoply_events`), or saves a menu
   group, header message or other translated snippet.
2. It goes on the `WaitingForEnglish` list. Draft saves don't count.
3. `manage.py translate_english` runs every minute on the server (a
   systemd timer). It sends only pieces without English to DeepL.
4. A nightly run at 03:30 catches up on anything still missing and
   deletes rows that are no longer needed.

Without `DEEPL_API_KEY` in `.env` (normal for local dev and tests),
nothing goes to DeepL. The details, timers and how to check on them are in
[management_commands.md](../../operations/management_commands.md#translate_english).

DeepL uses a glossary of fixed terms
(`translation/glossary_terms.py`, pushed with `sync_deepl_glossary`), so
for example union and tool names stay as they are.

Superusers can switch automatic translation off under **Settings →
Translation settings**.

## How editors work with English

- **English** button on a page or snippet (page header, listing "more"
  menu, snippet rows, and the "English" link in Editor mode): opens the
  English editor. It shows every piece as Norwegian | English, with its
  source and whether it is out of date. Saving stores the corrections as
  `human`. The page's English slug is edited at the top.
- **Machine-translate now** (in the English editor): asks DeepL right
  away, also when automatic translation is off.
- **Machine-translate subtree** (page header and "more" menu): queues a
  page and everything under it.
- **Machine-translate menu** (on `Menu` rows): translates all of a menu's
  groups and links in one go.
- **Preview** has two modes, Norsk and English. The English preview of a
  draft shows Norwegian for new text, because previews never call DeepL.
- Dashboard panel and page notices list pages whose English is missing or
  failed.
- **The admin's own language** follows its address: `/nb/wagtail-admin/`
  is Norwegian, `/en/wagtail-admin/` English. The "English" / "Norsk" item
  in the sidebar switches between them. A language picked in Account →
  Preferences overrides the address. The content in the admin is always
  the Norwegian you edit, whatever the admin's language.

## Adding or changing a field

Every page type and translated snippet lists the fields that have English
in `translated_fields`:

```python
class ToolPage(...):
    translated_fields = ["description"]
```

- Wagtail's own `title`, `seo_title` and `search_description` are added
  for every page automatically. Don't list them.
- Only list text meant for people. IDs, colour codes, URLs, emails, slugs
  and choice fields are refused at startup.
- Inside a StreamField, `untranslated_block_paths` keeps text blocks out,
  for example people's names: `untranslated_block_paths = ["sitting_members.*.name"]`.
- A test fails if a page type or translated snippet has no
  `translated_fields`.

`translation/translated_fields.json` lists every translated place on every
model. A test compares it with the models:

- **You added or removed a translated field on purpose:** run
  `python manage.py update_translation_snapshot` and commit the file.
- **Never change how fields are split into pieces.**
  `tests/test_segment_format.py` pins the exact pieces for example
  content. If it fails after a wagtail-localize upgrade, every stored
  English piece would stop matching; fix the extraction, don't update the
  test's file.
- **You renamed a field, or a field inside a block:** the stored English
  is keyed by the old name. Move it in the migration that renames the
  field. The failing test prints the exact line to add, which looks like:

  ```python
  from ifi_home_app.translation.stored_translations import rename_segment_path

  migrations.RunPython(
      lambda apps, schema_editor: rename_segment_path(
          apps, "ArticlePage", "body.*.caption", "body.*.image_caption"
      ),
      migrations.RunPython.noop,
  )
  ```

## Rules for code

- **Read fields normally.** `page.title`, `page.body`, `menu_group.title`
  and `page.url` give the right language. There is no `.localized` and no
  locale filter: only Norwegian rows exist.
- **Querying around the model shows Norwegian.** `.values("title")`,
  `.values_list()`, raw SQL and `annotate()` don't go through the fields,
  so they return Norwegian on `/en/`. Load objects instead when the text
  is shown to visitors. `tests/test_english_crawl.py` stores fake English
  for everything and crawls `/en/`, so a leak like this fails the tests.
- **Never save during display.** English is only switched on for
  `GET`/`HEAD` requests under `/en/` and for the English preview. While it
  is on, any write to a page, snippet or revision table is refused with
  `EnglishWriteBlocked`. If you hit that error, your code is saving
  something in a view that only shows a page. Move the save out of it;
  don't work around the error.
- Admin views, `POST` requests, commands and the timers always see
  Norwegian.
- `english_overlay.english()` switches English on in a test, and
  `raw_norwegian()` forces Norwegian inside it.

## Fixed texts in templates and code

Headings, buttons and other texts written by developers use Django's own
translation system, not the tables above:

1. Mark the text: `{% trans "Upcoming events" %}` in templates,
   `_("Upcoming events")` in Python.
2. Update the `.po` files and compile them. The commands are in
   [everyday_commands.md](../../contributing/everyday_commands.md#translations).

Write these texts in English and add the Norwegian in
`ifiplatform/locale/nb/`.

## Known gaps

- **Images are shared.** A poster with Norwegian text on it stays
  Norwegian on `/en/`.
- **No English search index.** The site has no public search. If one is
  added, it will need an index of the English text too.
- Both are listed in [to_fix.md](../../to_fix.md).
