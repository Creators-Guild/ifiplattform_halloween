# Community Goals (Claude draft — reference only)

Last updated: 2026-08-14

> **Note:** This is a Claude-authored draft kept as inspiration in `docs/claude_references/`. It is *not* the final doc — the intent is to write the real version by hand, using this (and the notes at the bottom) as a starting point, not to publish this text as-is.

IfiPlatform isn't just a product to ship — it's meant to grow through the students who use it. This doc lays out why community-building and low-threshold contribution are treated as a project goal in their own right, not just a nice side effect.

## Why this matters

- **This is a platform built by its own userbase.** IfiPlatform is a student platform, for IFI-students, built by IFI-students — the people writing the code and the people using the product are the same group. That's not incidental: it means contributors are improving something they themselves rely on, and it's part of why their input should shape the product directly rather than being routed around.
- **Students find problems developers don't.** People using the platform day-to-day will spot bugs, awkward flows, and rough design far faster than the (small) group of developers working on it. That's a resource going largely untapped without an easy way for users to surface what they notice.
- **Most students who'd want to contribute have little to no dev experience.** IFI has plenty of early-bachelor students who could contribute given a low enough barrier to entry, but "go read the codebase and open a PR" is not that barrier. The project should actively build entry points sized for a first-time contributor, not assume people will find their own way in.
- **Contributing here should help students get hired.** For a lot of contributors, this will be their first real-world codebase — a live product with actual users, review, and consequences, not a course assignment. Treating contribution as a place to build practical, CV-worthy experience (real PRs, real code review, real teamwork) is as much a goal as the code that gets produced.
- **Contribution should be rewarding, not just tolerated.** Reporting a bug or suggesting an idea should feel like it goes somewhere — reviewed, acted on, and visibly credited — rather than disappearing into an inbox. That feedback loop is what turns a one-off contribution into someone sticking around.

## What this looks like in practice

- Keeping the `good first issue` and `help wanted` labels genuinely stocked with approachable, well-scoped issues (see [CONTRIBUTING.md](../../CONTRIBUTING.md)), not just using them decoratively.
- In-app pathways for non-developers to contribute without touching code — e.g. a logged-in "report a bug" / "request a feature" flow that staff can turn into real GitHub issues, rather than requiring someone to already know GitHub exists to give feedback.
- Closing the loop with contributors: letting people see what happened to something they reported, instead of it seeming to go nowhere.
- Being upfront with non-users about what contributing looks like and why it's worth doing, not just gating it behind an account wall with no explanation.

## Relationship to the rest of the docs

This is a "why," not a "how" — for the technical architecture, see [docs/architecture/](../architecture/); for the actual process of contributing code, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## Wishes & key points to carry into the final version

Notes pulled from the conversation this draft came out of — the important points to keep even after rewriting this from scratch:

- **Students as the main target, open-community focus.** The core goal is community-building around the platform, with IFI students specifically as the audience to design for.
- **Low-threshold entry points, actively built.** Not just "contributions welcome" in theory — the project should actively find and build easy, low-effort ways in for students who want to help but don't know where to start.
- **"By students, for students" — own-userbase framing.** This is a student platform where the people building it and the people using it are the same group; call this out explicitly, it's not incidental.
- **Career/hireability angle.** Add contributing-as-practical-experience as an explicit goal — helping students build real, CV-worthy experience (real PRs, real review, real teamwork) as a benefit of contributing, not just a side effect.
- **Grew out of the feedback-feature discussion.** This doc was prompted by planning a bug-report/feature-request system (see the conversation / the filed GitHub issue for "Feedback Feature") — keep the tie-in to that concrete example when explaining *why* low-threshold contribution matters (students spot bugs/design issues faster than devs; reports need to visibly go somewhere and get closed-loop status updates so contributors feel a sense of achievement).
- **Tone:** written to match the existing welcoming tone already in `CONTRIBUTING.md` and the README's `## About` section — plain, direct, not corporate-sounding.
