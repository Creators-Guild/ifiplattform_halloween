# models/article/unions.py — design notes

Last updated: 2026-10-09
Covers: ifiplatform/apps/ifi_home_app/management/seed_dev_data/unions.py, ifiplatform/apps/ifi_home_app/models/article/unions.py

Context for future Claude sessions. Not a human-facing doc.

## UnionPage.get_context — the local import

`upcoming_events_for_union` is imported inside the method, not at module
level: `models/event/pages.py` imports `TranslationWarningMixin` (and other
symbols) from the `models.article_models` compatibility shim, which in
turn imports from this module — a module-level import the other way would
be circular.

## StudentUnionCategoryPage.union_groups

Editor-curated groupings (e.g. "Faglige foreninger"/"Sosiale foreninger")
shown above the automatic "All unions" listing. `get_context()`'s own
`unions` queryset still lists every live child `UnionPage` regardless of
grouping — a union placed in a group here isn't removed from that full
listing, the two are independent/additive, not a partition. Reuses
`union_card_block()` (the same "Student Union Card" block used inside
`ArticlePage`'s own body) rather than a second, parallel way of picking a
`UnionPage`.

## StudentUnionCategoryPage.get_context

`program_unions`/`other_unions` are both automatic, not editor-curated:
`program_unions` is every active union with `union_type="program"`;
`other_unions` is every active union that isn't program-specific *and*
isn't already placed in one of `union_groups`' own curated groups/rows —
so a union never ends up listed in "Andre foreninger" alongside its own
more specific section.

## UnionPage.sitting_members -- the "member" block, filled_positions, open_positions

The block type is still named `"member"`, and `role`/`school_email`/
`picture` kept their original field names when `name`/`role_nickname`/
`availability`/`availability_note` were added -- renaming any of these
would orphan already-saved StreamField JSON, since Wagtail matches stored
block data by these exact names. `name` is optional now: a blank name is a
vacant position, not a data-entry mistake.

`description` (a single `RichTextBlock`) was replaced with
`responsibilities` (a `ListBlock(RichTextBlock(features=["bold", "italic"]))`,
one short item per responsibility, formatting limited to bold/italic --
no links/lists within an item) -- see migration `0148_migrate_union_
position_description_to_responsibilities.py` for the one-time copy of each
position's old description text (HTML stripped) into the first
responsibility item, and `0150_alter_unionpage_sitting_members.py` for the
later CharBlock -> RichTextBlock upgrade (schema-only -- existing plain-
text items are valid RichText source as-is, no data migration needed).
`description` itself was removed from the block rather than kept alongside
-- any leftover `description` key in old stored JSON is simply ignored by
the current block definition (StructBlock.to_python() only reads fields it
knows about), not a live/rendered field any more.

`filled_positions` and `open_positions` (properties on `UnionPage`) are
independent filters over the same `sitting_members` list, not a
partition -- a block with both a `name` set and `availability` other than
`"filled"` shows up in both (a seat that's currently held but opening up
at the next generalforsamling). `open_positions` renders `responsibilities`
inline on the card (the point of that row is "what does this role need,"
so it shouldn't take an extra click); `filled_positions` puts it behind
the info-icon popup instead (`union_position_info.js`, same
icon-button-toggles-a-panel pattern as `table_of_content.js`/`.toc-widget`)
since showing every responsibility on every currently-filled seat's card
would be clutter there.

### Navet's seed sitting_members (seed_dev_data/unions.py)

`_navet_sitting_members` deliberately covers all four combinations of
filled/open x all-fields-set/optional-fields-blank, since Navet is the
project's designated main test union (also pinned in the seeded Student
Unions menu group, see seed_dev_data/menus.py, plus fake
contact/social/member-count data so its sidebar isn't empty).

### Deferred: linking a position to a real user account

Discussed but not built: letting `sitting_members` link a position to an
actual `User` instead of typing a name by hand. Deferred because there's
no public profile page yet for such a link to point to, and it's real
scope on its own -- captured here so it isn't rediscovered from scratch:

- No block-level "pick a user" pattern exists anywhere in this codebase.
  `User` isn't a Wagtail Page or a registered snippet, so
  `PageChooserBlock`/`SnippetChooserBlock` don't apply as-is; registering
  `User` as a snippet solely to unlock `SnippetChooserBlock` would create
  a second, conflicting admin surface alongside `wagtail.users`' own. The
  intended shape was a small custom `Block` subclass wrapping a plain
  `forms.ModelChoiceField` (a `<select>`, not a chooser modal -- Wagtail
  7.4's `ChooserViewSet` could build a nicer modal later if the user list
  grows large enough to need search).
- `ArticlePage.author` (`article/pages.py`) is the closest existing
  precedent -- a plain FK with an `author_attribution` choice
  (real name vs. `Profile.nickname`) picked *per article* by whoever
  wrote it -- but that pattern doesn't fit here: for a linked union
  position, the account owner should control whether their real name or
  nickname displays, not whoever happens to be editing the union page.
  That needs a new *global* preference on `Profile`
  (e.g. `display_preference`), separate from `author_attribution`, plus
  the corresponding account-settings UI.
