# Contributing to IfiPlatform

Thanks for wanting to contribute! IfiPlatform is built by IFI-Creators' Guild, and contributions of any size are welcome: a typo, a bug report or a whole feature.

Never contributed to an open source project before? This guide walks you through it.

**On this page:** [Set up](#1-set-up-once) · [Make a change](#2-make-a-change-step-by-step) · [Good pull requests](#good-pull-requests) · [Code style](#code-style) · [Reporting an issue](#reporting-an-issue) · [Who can contribute](#who-can-contribute) · [Questions](#questions)

## 1. Set up (once)

Follow [Get started](README.md#get-started) in the README. When the site runs at http://localhost:8000, come back here.

**Not used to Git in the terminal?** Install [GitHub Desktop](https://desktop.github.com/). It does branches, commits, pushes and pull requests with buttons.

## 2. Make a change, step by step

> **New to Git?** See the Git and GitHub section in [TUTORIALS.md](TUTORIALS.md).

Do this for every change. There are two ways to do the Git parts. Pick the one you like:

- **[With commands in the terminal](#with-commands-in-the-terminal):** the steps below.
- **[With GitHub Desktop](#with-github-desktop):** the same steps, but steps 2, 5, 6 and 7 use buttons instead of commands.

### With commands in the terminal

1. **Pick an issue.**
   Start with one labeled `good first issue` in the [Issues tab](../../issues). Comment that you're taking it.

2. **Make a branch** for that issue.

   ```bash
   git fetch upstream
   git switch -c <type>/<few-words> upstream/main
   ```

   - `git fetch upstream` downloads everyone's latest changes from the main repo. It doesn't change your files yet.
   - `git switch -c <type>/<few-words> upstream/main` makes a new branch, starting from that latest `main`, and switches to it. `-c` means "create".

   `<type>` is the issue's Type: `bug`, `feature` or `task`. For example `bug/login-redirect` or `feature/mobile-nav`.

   **Using the `ifi` commands?** `ifi fix-issue <issue number>` does this step for you and names the branch from the issue. In step 6, `ifi save "message"` adds and commits everything, and in step 7 `ifi pull-request` pushes and prints the pull request link. Your branch fell behind `main`? `ifi update`. Something odd? `ifi check`.

3. **Make your change.**
   Not sure which file to open? See [Where do I change…?](docs/contributing/how_this_project_works.md#where-do-i-change). The site at http://localhost:8000 reloads when you save.

4. **Run the quick tests.**

   ```bash
   python manage.py test --exclude-tag=slow
   ```

5. **Check your files** with `git status` (or the Source Control panel in VS Code).
   Only the files you meant to change should be listed. See others? Ask before committing.

6. **Commit and push.**

   ```bash
   git add .
   git commit -m "Short description of what you changed"
   git push -u origin <your-branch-name>
   ```

   `git add .` adds every file `git status` listed in step 5, so do that check first.

   Asked to log in, or "Please tell me who you are"? See [Log in to GitHub](docs/contributing/get_the_code.md#log-in-to-github-once).

7. **Open a pull request.**
   Click **Compare & pull request** on GitHub. The description box is filled with a short template: write what you changed and why, add `Closes #<issue number>`, and tick the checklist.

8. **Answer review comments.**
   To update your pull request, commit and push to the same branch again.

### With GitHub Desktop

The same steps, with buttons instead of commands:

| Step | In GitHub Desktop |
| --- | --- |
| 2. Make a branch | **Fetch origin**, then **Current Branch → New Branch**. Base it on **upstream/main** |
| 5. Check your files | The **Changes** tab lists every changed file. Untick the ones you didn't mean to change |
| 6. Commit and push | Write a summary at the bottom left, click **Commit to *your-branch***, then **Publish branch** (later: **Push origin**) |
| 7. Open a pull request | Click **Create Pull Request**. GitHub opens in your browser |
## Good pull requests

- **One issue per pull request.** Small and focused is much easier to review.
- **Commit in small steps.** Commit each time one piece works, with a message that says what it does: `Add date to event card`, not `fix`.
- **Update your branch** before you open the pull request:

  ```bash
  git fetch upstream
  git rebase upstream/main
  ```

- **Not finished yet?** Open it as a **draft pull request** to get early feedback.
- **Review comments are normal.** Everyone gets them. They're about the code, not about you.

## Code style

- Follow the style and naming of the code around you.
- Keep functions focused: one job each, where reasonable.
- Comment what isn't obvious. Skip comments that only repeat the code.

**Formatting: Black.** VS Code formats Python files when you save, with or without Docker. CI checks every pull request with `black --check` and fails if a file isn't formatted. In other editors, run `black .` from the repo root before committing.

**Linting: Pylint.** VS Code underlines problems while you type. CI runs Pylint on every pull request to `main`, and it must score **7/10 or higher** to pass. To run the same check as CI, run this from the repo root in a bash terminal (the container terminal works; PowerShell doesn't):

```bash
pylint --load-plugins pylint_django --django-settings-module=ifiplatform_project.settings --ignore-paths=ifiplatform/.*/migrations --fail-under=7 $(git ls-files '*.py')
```

**Editor settings.** `.vscode/settings.json` is shared by everyone. Put your own preferences under the **User** tab in VS Code's settings, not **Workspace**, so they stay out of your pull request.

## Reporting an issue

**Search the existing issues first**, so you don't report the same thing twice.

Every issue gets one **Type**:

| Type | Use for |
| --- | --- |
| **Bug** | Something is broken or doesn't work as expected |
| **Feature** | New functionality or a user-facing improvement |
| **Task** | Maintenance, cleanup, tooling, dependency updates, sub-tasks, tests and documentation |

Then add **labels** for detail:

| Label | Means |
| --- | --- |
| `good first issue` | A good place to start if you're new |
| `help wanted` | We'd especially like outside help |
| `test` | About writing or improving tests |
| `docs` | About documentation |
| `area: ui`, `area: mobile`, `area: backend`, … | Which part of the platform it touches |

Example: tests for the login page are **Type: Task** with the labels `test` and `area: backend`.

**Writing it:** copy the structure of the pinned `example` issues in the [Issues tab](../../issues) (one each for Bug, Feature and Task), and leave out what doesn't apply. Whoever picks it up doesn't know what you know. **When in doubt, overexplain.**

## Who can contribute

**Anyone** can open issues and pull requests. No special access needed.

| Role | Who | Can |
| --- | --- | --- |
| **Contributor** (you) | Anyone | Fork the repo, open issues and pull requests |
| **Collaborator** ([guide](docs/contributing/collaborators.md)) | Trusted IFI-Creators' Guild members | Push branches to the main repo and manage issues |
| **Committer** | The core team | Review and merge into the main repo |

- **Pull requests are merged** from current students at the Department of Informatics (UiO), or from people approved by IFI-Creators' Guild.
- **Roles grow with trust.** Guild members who do consistent, good work can be invited to become Collaborators, and later Committers. Want write access? Ask a Committer.
- **Not eligible?** You're still welcome. A Committer will merge your pull request if it's a good fit, but it may not be prioritised.

## Questions?

- **Something here is unclear?** Open an issue with **Type: Task** and the label `docs`. Improving this guide is a contribution too.
- **Email the core team:** hkniemi@uio.no
- When in doubt, ask Claude.
