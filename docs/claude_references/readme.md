# docs/claude_references/ — what this is

Last updated: 2026-09-29

This folder holds **Claude-authored drafts kept as inspiration** — a
starting point for a real, human-facing doc (a README-style guide, a
project-values writeup, a proposal), not the final version of anything.
Nothing in here is authoritative or meant to be linked to as if it were
finished. Each draft's `Last updated:` date shows when it was written or
last changed. The code and the project may have moved on since then, so
check the facts in a draft before you reuse them.

## Why drafts live here instead of just being the doc

Writing a first draft of a doc is often the slow part; getting from a
rough draft to something worth publishing is a smaller step. Keeping
Claude's draft in its own folder, clearly labeled as a draft, means:

- No one mistakes it for the real, decided-on version of a policy or guide.
- Whoever picks it up to finish it can freely restructure, cut, or rewrite
  without worrying about "changing something official."
- It's obvious at a glance (by folder alone) which docs in this repo are
  finished and which are still someone's homework.

## What to do with a file in here

Rewrite it by hand into the real thing — a root-level doc (`README.md`,
`CONTRIBUTING.md`, `TUTORIALS.md`) or a topic doc under `docs/` — using the
draft as a starting point, not something to publish as-is. Once rewritten,
**move the result out of this folder**; don't leave a finished doc living
here alongside the drafts. See each draft's own "Wishes & key points to
carry into the final version" section (if it has one) for what the person
who requested it said mattered most to keep.

## If you're Claude, asked to draft a new doc

Put it here, with the same header every existing file in this folder uses:
a `# Title (Claude draft — reference only)` heading and a note pointing
back to this file. See [writing_guidelines.md](writing_guidelines.md) for
the tone/structure/audience this repo's docs are written for — apply it to
whatever you draft. Lowercase `snake_case.md` naming, matching the existing
files here (`community_goals.md`, `writing_guidelines.md`).

## Not to be confused with docs/claude_context/

[docs/claude_context/](../claude_context/readme_claude.md) looks similar
but serves the opposite purpose: permanent, technical, AI-facing
implementation notes that are never meant to become a human doc. This
folder is temporary drafts of human docs; that one is permanent context
for an AI editing code. If what you're writing is "why this code works
this way," it belongs there, not here.
