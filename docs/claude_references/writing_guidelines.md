# Writing Docs (Claude draft — reference only)

Last updated: 2026-08-15

> **Note:** This is a Claude-authored draft kept as inspiration in `docs/claude_references/`. It is *not* the final doc — write the real version by hand, using this as a starting point rather than publishing it as-is.

Guidelines for writing documentation in this repo — READMEs, CONTRIBUTING-style guides, `docs/` files, issue write-ups. Aimed squarely at students, many of whom are writing project documentation, or contributing to a real codebase, for the first time.

## Who you're writing for

Assume the reader:
- Might be a first-year student who's never touched this codebase, or open source at all.
- Doesn't share your context — they don't know what you were thinking when you wrote this, what problem prompted it, or what's "obvious" to you.
- May not be a native English speaker (the platform itself is bilingual, nb/en) — keep sentences straightforward.

## Tone

- Plain and direct, not corporate. Write like you're explaining something to a classmate, not filing a compliance report.
- Friendly but not fluffy — skip hype language ("game-changing", "seamless", "empower"). Say what the thing actually does.
- It's fine to be informal (see `CONTRIBUTING.md`'s "I know, I'm sorry;_;" aside) as long as it doesn't get in the way of clarity.

## Overexplain rather than underexplain

This is already the standard for this repo's issue templates and `CONTRIBUTING.md` — apply it to all docs:

> "Don't assume something is obvious — overexplain rather than underexplain."

Concretely: spell out acronyms/jargon the first time (or link to where they're explained), state the *why* and not just the *what*, and don't assume the reader already knows internal terms — like "Committer" or "wagtail-localize" — without a pointer to where those are actually defined.

## Structure

- Lead with the shortest possible summary of what the doc is for, before diving into details.
- Use headers (`##`, `###`) to make docs skimmable — most readers scan before they read.
- Prefer short bullet lists over dense paragraphs where the content is naturally a list.
- Code blocks get a language hint (` ```bash `, ` ```python `, etc.) even for trivial commands.
- Link instead of duplicating: if something's explained elsewhere (e.g. Setup in `README.md`), link to it rather than re-explaining it.

## Where things live

- Root-level docs (`README.md`, `CONTRIBUTING.md`, `TUTORIALS.md`) — things every contributor needs, regardless of what they're working on.
- `docs/architecture/`, `docs/design/` — technical/visual references tied to a specific area.
- `docs/claude_references/` — AI-drafted starting points kept as inspiration, not meant to be the final, authoritative version of anything. If you rewrite one into something real, move the result out of that folder. See [readme.md](readme.md) in this folder for the full convention.
- New top-level topic docs go directly under `docs/`.

## File naming

Lowercase `snake_case.md`, matching the existing files in `docs/` (e.g. `community_goals.md`, `eraser_links.md`).

## Before you open the PR

- Read it once as if you're the target reader — a student who just found this repo. Does it actually make sense without the context you already have in your head?
- Cross-check any commands/paths you wrote actually work (copy-paste them if you can, rather than typing from memory).
- If in doubt about tone or whether something needs more explanation, ask — see the Questions section in [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## Wishes & key points to carry into the final version

- This guideline exists because docs here are written for students, often first-time contributors — the tone guidance should stay grounded in that, not turn into a generic style guide.
- The "overexplain rather than underexplain" line is already an established project value (from `CONTRIBUTING.md` and the issue templates) — worth keeping front and center rather than introducing new phrasing for the same idea.
- Keep it short enough that someone will actually read it before writing their first doc PR.
