# ifi_home_app migrations — gotchas

Last updated: 2026-09-29
Covers: ifiplatform/apps/ifi_home_app/migrations/0089_merge_paragraph_styled_text.py, ifiplatform/apps/ifi_home_app/migrations/0090_fix_revision_content_type_and_body_shape.py, ifiplatform/apps/ifi_home_app/migrations/0093_articleblockstyle_finalize_translation_key.py

Lessons from real data-loss bugs in this app's migrations. The migrations
listed above carry the full per-migration story in their own docstrings;
this note is the general rules to apply to *future* migrations.

## Renaming or removing a StreamField block type: use raw SQL

Wagtail's `StreamBlock.to_python()` silently drops any **top-level** stream
child whose `"type"` isn't in the *current* schema's `child_blocks`, the
moment the field is loaded. A data migration that reads `page.body` (or
`page.body.raw_data`) through the ORM — even a historical
`apps.get_model()` instance — has already lost the renamed/removed blocks
before its own code runs. Nested content (e.g. inside a `multi_column`
column) is resolved lazily and is not affected.

Pattern (see 0089): read and write `ArticlePage.body` with raw SQL via
`schema_editor.connection.cursor()`, and transform the raw JSON with
`wagtail.blocks.migrations.operations` /
`utils.apply_changes_to_raw_data`.

Treat any StreamField-shape-changing migration as high risk: dry-run the
transform against a DB copy, check that `ArticleBlockStyle` overrides still
match by block id afterwards, and render every changed page (not just
`manage.py check`).

## Touching `Revision.content`

Found the day after 0089 shipped, via a live report of text disappearing on
save in the Wagtail admin (fixed by 0090):

1. Filter revisions by `content_type`, **never** `base_content_type`.
   `base_content_type` is always `wagtailcore.page`, so filtering on the
   subclass's content type matches zero rows, silently.
2. `revision.content["body"]` is a JSON-encoded **string**, not a parsed
   list. It needs an explicit `json.loads()` / `json.dumps()` round trip.
   The live `ArticlePage.body` column doesn't have this quirk.

Why it matters: the Wagtail admin editor loads the *latest revision*, not
the live row. A revision left in an old block shape renders as an empty
widget, and saving writes that emptiness back. This project's own
`publish_page` view (publishes `get_latest_revision()`) can also push a
stale revision onto the live row.

Write revision fixers to be **idempotent**: check each block's current
shape before changing it. `wagtail.blocks.migrations` operations match on
type alone and would double-wrap already-fixed blocks. 0090 is the example.

Known leftover, not fixed: about 180 revisions still hold a `"box"` block
type removed by `0077_unwrap_box_blocks`. It's the same latent bug shape.
Fix it with the same pattern if it ever surfaces.

## Data-consolidating migrations are forward-only

On SQLite, `RemoveField`/`AlterField` are done by rebuilding the table.
Reversing a `RemoveField` of a FK (0093 dropped `ArticleBlockStyle.article`
after 0092 backfilled `translation_key` and deduplicated rows) re-adds the
column **empty**, because nothing captured the old values. Reversing
further then fails on `NOT NULL`, but each migration is its own transaction
on SQLite, so the emptied column is already committed. Data is gone.

Rules:
- Don't test-reverse a migration chain that removes a field made redundant
  by an earlier data migration, especially one with a non-reversible step
  like a dedup that deletes rows.
- Say "forward-only" in such a migration's docstring instead of relying on
  Django's auto-generated reverse.
- If it happens anyway: restore from a pre-migration backup and migrate
  forward again. Don't try to patch the reverse path in place.
