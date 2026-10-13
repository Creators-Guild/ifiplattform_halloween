# Contributing to IfiPlatform
 
Thanks for wanting to contribute! This project is built by IFI-Creators' Guild — contributions of any size are welcome, whether it's fixing a typo, reporting a bug, or building a new feature.
 
If you've never contributed to an open source project before, don't worry — this guide walks through everything you need.

## Getting Started
 
1. **Fork, clone and set up** by following the [Quick start in the README](README.md#quick-start). It forks the repo, clones your fork, connects the `upstream` remote this guide uses, and starts the site in Docker. Can't use Docker? See [setup without Docker](docs/contributing/setup_without_docker.md). Collaborators with write access clone the main repo directly and use `origin` wherever this guide says `upstream`.
2. **Get the latest code and create a branch** for your change:
```bash
git fetch upstream
git checkout -b <issue-type>/<short-description> upstream/main
```
   e.g. `feature/mobile-nav`, `bug/login-redirect`, `task/setup-instructions`

## Your First Contribution, Step by Step

1. **Pick an issue** labeled `good first issue` in the [Issues tab](../../issues). Leave a comment saying you're taking it, so nobody else starts on the same thing.
2. **Get the latest code and make a branch** (step 2 above).
3. **Make your change.** The site at http://localhost:8000 reloads when you save a file, so you can check your change in the browser right away.
4. **Run the quick tests:**
```bash
python manage.py test --exclude-tag=slow
```
5. **Check what you're about to commit** with `git status` (or the Source Control panel in VS Code). Only the files you meant to change should be listed. If you see files you didn't touch, ask before committing.
6. **Commit and push.** You can commit several times before you push (see *Commit in small steps* below):
```bash
git add <the files you changed>
git commit -m "Short description of what you changed"
git push -u origin <your-branch-name>
```
7. **Open a pull request.** GitHub shows a "Compare & pull request" button after you push. The description box is filled with a short template: write what you changed and why, add `Closes #<issue number>`, and tick the checklist.
8. **Answer review comments.** To update your PR, commit and push to the same branch again.

New to Git? See the Git and GitHub section in [TUTORIALS.md](TUTORIALS.md).

## Main Roles in this Repository
1. **Committer** - Trusted developer (and part of core team) with the rights to commit and merge code directly to the main repository
2. **Collaborator** - Developer with write access to the repo itself (e.g. teammates who aren't yet trusted to merge unreviewed, but can push branches and manage issues directly)
3. **Contributor (You)** - The open, public-facing role — anyone can be this without any special access. You fork the repo, open issues, and submit pull requests for review.

**These roles aren't fixed** — As long as you are a member of IFI-Creators' Guild, contributors who show consistent, quality work may be invited to become Collaborators, and Collaborators who build up trust over time may be invited to become Committers.

## Who Can Contribute
 
As described in **Main Roles** above, anyone can be a **Contributor** — no special access needed. Open an issue, fork the repo, and submit a pull request whenever you like; we welcome outside eyes on bugs or ideas from anyone, IFI student or not.
 
However, to keep **merged code and write access** within our intended community, PRs are only merged from contributors who are either:
- A current student at the Department of Informatics, University of Oslo, or
- Approved by IFI-Creators' Guild
If you're eligible and want write access (to push branches directly, manage issues, etc.) rather than working from a fork, reach out to a **Committer** to apply to get set up as a Collaborator.
 
If you're not currently eligible, you're still welcome to open issues and submit PRs from a fork as a Contributor — a Committer will review and merge on your behalf if the contribution is a good fit. However, note that you are not likely to be prioritized unless the contribution is of high value to the project.
 
## Reporting Issues
 
Before opening a new issue, please **search existing issues** to check it hasn't already been reported.
 
### Issue Type
 
We use GitHub's native **Issue Type** field with three options:
 
| Type | Use for |
|---|---|
| **Bug** | Something is broken or not working as expected |
| **Feature** | New functionality or user-facing improvement |
| **Task** | Maintenance, chores, cleanup, tooling, dependency updates, sub-tasks, tests, and documentation |
 
### Labels
 
On top of Type, we use labels to add detail:
 
- `test` — issue is specifically about writing or improving test coverage
- `docs` — issue is specifically about documentation
- `area: mobile`, `area: ui`, `area: backend`, etc. — which part of the platform it touches
- `good first issue` — a good entry point if you're new to the project
- `help wanted` — we'd especially appreciate outside help on this one
**Example:** an issue about adding tests for the login page would be **Type: Task** + labels `test`, `area: backend`.
 
### Example issue templates
 
We keep worked examples of how to write a good issue for each type — check the pinned/labeled `example` issues in the [Issues tab](../../issues) for a Bug, Feature, and Task example you can copy the structure from. Take what's relevant to your issue and leave out what isn't; not every field applies to every issue. 

There are no rules you have to follow regarding the templates, but it is **highly recommended**. This is to ensure that issues are well documented, easy to understand and pick up by others. Don't assume something is obvious — you already know the context behind this issue, but someone picking it up might not. **When in doubt, overexplain rather than underexplain.**
 
## Submitting a Pull Request
 
1. Make sure your branch is up to date with the main repo's `main` before opening a PR (collaborators: `origin` instead of `upstream`):
```bash
git fetch upstream
git rebase upstream/main
```
2. Keep PRs **small and focused** — one bug fix or one feature per PR is much easier to review than a large bundle of unrelated changes.
3. **Commit in small steps.** Make a commit each time one piece works, with a message that says what it does (`Add date to event card`, not `fix` or `changes`). One big commit at the end is hard to review, and if something breaks, small commits make it easy to find and undo the one that caused it. Small doesn't mean tiny: one commit per typo is too much.
4. Write a clear PR description: what you changed, why, and which issue it relates to (e.g. `Closes #12`).
5. If your change isn't finished yet but you want early feedback, open it as a **draft PR**.
6. Be responsive to review comments — feedback is about the code, not about you. Everyone's PRs get review comments; it's a normal part of the process, not a sign something went wrong.

## Code Style
 
- Follow existing formatting/naming conventions in the codebase.
- Keep functions and views focused — one responsibility per function where reasonable.
- Comment non-obvious logic, but don't over-comment self-explanatory code.

**Formatting:** We use [Black](https://black.readthedocs.io/) to auto-format code. It's included in `requirements.txt`, so it's installed automatically as part of your setup. In VS Code (with or without Docker), Black formats a Python file every time you save it, so you don't need to do anything. CI checks every pull request with `black --check` and fails if a file isn't formatted. In other editors, run this from the repo root before committing:
```bash
black .
```
 
**Linting:** Pylint runs automatically in CI on every pull request to `main` and must score **7/10 or higher** to pass. In VS Code, pylint runs while you type and underlines problems. To run the same check as CI, run this from the repo root in a bash terminal (the container terminal works; PowerShell doesn't):
```bash
pylint --load-plugins pylint_django --django-settings-module=ifiplatform_project.settings --ignore-paths=ifiplatform/.*/migrations --fail-under=7 $(git ls-files '*.py')
```

**Editor settings:** `.vscode/settings.json` is shared by everyone working on the project. Change your personal preferences under the **User** tab in VS Code's settings, not the **Workspace** tab, so they don't end up in your PR.

 
## Questions?
 
If anything here is unclear, open an issue with **Type: Task** and label `docs` — improving this guide for the next contributor is a contribution too.

Else, send a mail to one of the core team:
- hkniemi@uio.no

When in doubt, ask Claude
