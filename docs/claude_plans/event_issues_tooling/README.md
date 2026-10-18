# Event issue tooling (Commit for Candy)

Everything to edit, test and post the event issues. The plan and the
decisions behind it are in [../event_issues_plan.md](../event_issues_plan.md):
read its "Current state" first. Run all commands from the repo root.

## What's here

| Path | What it is |
| --- | --- |
| `issues/<ID>.md` | One issue each: front matter (id, title, size, category, type, parent set, knowledge, minutes), then the body. `SET-*` are the set parents. **Edit issues here.** |
| `solutions/<ID>/` | The solution as files at their repo paths. `phase1_solutions/*.patch` are the phase 1 solutions as diffs. |
| `helper_notes.py` | The helpers' note per issue (shown with the solution on the site). |
| `generate.py` | Builds `out/bodies/<ID>.md` (final issue texts: reward, time, knowledge, set, text, how-to block) and `out/solutions_by_id.json` (notes + diffs from `pilot_repo`). |
| `check_issue_files.py` | Fails if a file is listed by two issues, an "edit" file is missing, or a "new:" file already exists. |
| `build_pilot_repo.sh` | Rebuilds `pilot_repo/`: the repo as it is now as `scaffold-base`, one branch per issue, and `all-merged` (the conflict test). Checks each branch changes exactly its listed files. |
| `build_review_doc.py` | Writes `../event_issues_<size>.md` (one doc per size: candy, chocolate, pumpkin) with a screenshot per issue. |
| `make_shot_env.sh`, `fetch_debs.py`, `shoot.py` | Screenshots without root: headless Chromium plus its libraries and fonts, then one screenshot per issue from `pilot_repo` served on port 8011. |
| `create_issues.py` | Posts the issues to GitHub with `gh` (labels, type, sub-issues, real numbers), and writes `out/solutions.json` for `load_event_solutions`. |

`pilot_repo/`, `out/`, `shots/`, `pwenv/` and `debs/` are generated and
ignored by git.

## After changing an issue or a solution

```bash
python3 -I docs/claude_plans/event_issues_tooling/check_issue_files.py .    # no shared files, paths as expected
docs/claude_plans/event_issues_tooling/build_pilot_repo.sh                  # all branches merge, file lists match
(cd docs/claude_plans/event_issues_tooling/pilot_repo/ifiplatform && python manage.py test --exclude-tag=slow --parallel)
python3 docs/claude_plans/event_issues_tooling/generate.py                  # final texts + helper solutions
```

A change to the scaffold (anything outside an issue's files) means
rebuilding `pilot_repo` too, since `scaffold-base` is the repo as it is now.

To test one solution on its own (the merge test only checks them all
together), use a worktree, so `pilot_repo` can stay on `all-merged`:

```bash
git -C docs/claude_plans/event_issues_tooling/pilot_repo worktree add /tmp/wt scaffold-base
cp ifiplatform/.env /tmp/wt/ifiplatform/
cd /tmp/wt && git checkout Q21 && (cd ifiplatform && python manage.py test --exclude-tag=slow)
```

Remove the worktree before running `build_pilot_repo.sh` again: the
script deletes `pilot_repo`, and the worktree with it.

## New screenshots for the review doc

```bash
docs/claude_plans/event_issues_tooling/make_shot_env.sh                     # once: about 250 MB, no root needed
(cd docs/claude_plans/event_issues_tooling/pilot_repo/ifiplatform && python manage.py runserver 127.0.0.1:8011 --noreload) &
source docs/claude_plans/event_issues_tooling/shot_env.sh && docs/claude_plans/event_issues_tooling/pwenv/bin/python docs/claude_plans/event_issues_tooling/shoot.py docs/claude_plans/event_issues_tooling/shots
python3 docs/claude_plans/event_issues_tooling/build_review_doc.py docs/claude_plans   # writes docs/claude_plans/event_issues_{candy,chocolate,pumpkin}.md
```

`shoot.py` has one recipe per issue: a page and a part of it to crop. A
new issue needs a recipe there, or it gets no picture. Two things that
trip recipes up: the site scrolls `body`, not the window (so
`window.scrollTo` does nothing: crop with a selector, which scrolls by
itself), and headless Chromium reports no mouse (`pointer: fine` is false),
so mouse-only features need the `matchMedia` override the Q18 recipe uses. Look at the
screenshots before trusting a solution: they found three broken ones.

## Posting to GitHub

Run on a computer where `gh auth login` is done (not in the container).
Check first whether any of these issues already exist on GitHub, since the
script would make them again.

```bash
python3 docs/claude_plans/event_issues_tooling/create_issues.py --repo Creators-Guild/ifiplattform_halloween --dry-run
python3 docs/claude_plans/event_issues_tooling/create_issues.py --repo Creators-Guild/ifiplattform_halloween
docker compose exec -T web python manage.py load_event_solutions < docs/claude_plans/event_issues_tooling/out/solutions.json
```

`out/` isn't in git, so that computer needs it too: copy this folder's
`out/` over, or commit, pull and run `build_pilot_repo.sh` and
`generate.py` there.

Afterwards, keep `out/numbers.json` (ID -> issue number) somewhere safe:
without it, a new run makes every issue again. To change posted issues, edit
`issues/`, run `generate.py`, and run `create_issues.py` again: it updates
every title and body, skips the sub-issues the sets already have, and
writes a new `solutions.json` to load again. Labels and type are only set
when an issue is created, removed issues aren't closed, and edits made on
GitHub are overwritten.

## Conventions in the issue texts

- Exact file paths under "### Files to change (only these)", one per bullet,
  `new:` for files to create. The Files check workflow reads this list.
- Code blocks close on their own line (` ``` `), never glued to the code.
- The explanation after solution code goes under `#### Explanation (optional)`.
- Design-heavy issues have a "### Design to build" section; "### Make it
  yours" holds alternatives.
- Borders in designs and solutions: `2px solid #000`, same thickness all
  round; the message board, news box, news cards and Instagram box have none.
