# Notes for AI agents

## Design notes (`docs/claude_context/`)

- Before editing a file, check its module docstring or top comment for a
  `docs/claude_context/...` pointer. If there is one, read that note first.
  How to write notes: `docs/claude_context/readme_claude.md`.
- **Stale check.** Each note starts with `Last updated:` and `Covers:`.
  Run `git log --since=<Last updated> --oneline -p -- <Covers paths>`.
  - Nothing that touches what the note explains: the note is fine. If
    there were commits, bump its date.
  - A change affects the note: fix the note and bump the date before
    relying on it.
- If you change a covered file in a way that affects its note, update the
  note and its date in the same task.

## Human docs

- Everything in `docs/` except the `claude_*` folders is for people. Follow
  the rules in `docs/README.md`, including a `Last updated:` date on every
  doc.
- Human docs never link to the claude folders. The one exception is the
  root `README.md`'s link to `docs/claude_references/`.

## Project rules

- Migrations that rename or remove a StreamField block type must read and
  write the field with raw SQL. Migrations that touch `Revision.content`
  must filter on `content_type`, never `base_content_type`.
  Data-consolidating migrations are forward-only: don't test-reverse them
  on SQLite. Details: `docs/claude_context/migrations.md`.
- The home templates crash with `ValueError` if the info-articles or news
  `ArticleIndexPage` is missing in a locale (this happened to prod `nb` in
  Aug 2026). The `{% if %}` guards were deliberately deferred. Don't add
  them unless asked.
- CSS: no comments unless one short line is truly needed. Prefer native
  HTML/CSS over JavaScript.

## Running the test suite

Don't reflexively run `manage.py test` after every change. For a small or
purely cosmetic edit — CSS (spacing, alignment, color), copy/text changes,
comment/docstring-only edits, template markup that doesn't touch template
logic — running the full suite (or even a scoped one) burns real time and
resources for a change the suite was never going to catch anything in.
Save it for changes that could actually break something: model/field
changes, template *logic* (a new `{% if %}`, a changed queryset/property),
view/command behavior, migrations. When in doubt, running one quick,
narrowly-scoped test is cheaper than the full suite.
