# Porting these files to IfiPlatform

Last updated: 2026-10-26

The setup and onboarding docs from the Halloween repo, with the event parts
taken out, and the tooling they rely on: the `ifi` commands and the Docker /
VS Code setup. Every path here is the same path in IfiPlatform, so you can
copy the folder's contents over the repo root. Don't copy this `PORTING.md`
itself.

**Base:** made against IfiPlatform's `task/dockersetup-for-server`
(`c5fba9e`, unchanged since 14 Oct). The docs link to that branch's
`docs/operations/docker_server.md`, `Dockerfile` and `compose.prod.yml`, and
`settings.py` here is that branch's file with two additions. So apply this on
top of that branch, or after it's merged. If main's `settings.py` changed in
the meantime, add the two blocks by hand instead (see below).

**Source:** the Halloween repo's `task/onboarding-process` at `d0b8615`
(26 Oct). Updated from the first version of this folder (20 Oct).

## What to do in IfiPlatform

1. Copy everything except this file over the repo root. Keep the Git file
   mode: every script in `tools/ifi/` and `ifi` must stay executable
   (`100755`). The test `commands_are_executable_in_git` checks it.
2. Delete `docs/contributing/docker.md`. `docs/contributing/docker_guide.md` replaces it.
3. In `docs/operations/docker_server.md` (line 11), change the link
   `contributing/docker.md` to `contributing/docker_guide.md`.
4. Rebuild the dev container, which is needed for the new `Dockerfile.dev`.
   The old `ifiplatform/media` is copied into the new `media` volume on the
   first start.

## Files

**New**
| File | What it is |
| --- | --- |
| `docs/contributing/get_the_code.md` | Fork (contributors) or clone (collaborators), logging in to GitHub, GitHub Desktop |
| `docs/contributing/setup_with_docker.md` | First-time Docker setup (was the README's Quick start) |
| `docs/contributing/docker_guide.md` | Replaces `docker.md`: how Docker works here, restart/rebuild/reset, `.env`, another GitHub account, the Claude Code login, problems |
| `docs/contributing/how_this_project_works.md` | Beginner's map: Django in plain words, folders, "where do I change…?" |
| `docs/contributing/collaborators.md` | The same steps with `origin` instead of `upstream` |
| `docs/contributing/images/*.svg` | The fork and clone diagrams |
| `docs/claude_context/ifi_account.md`, `dev_container_users.md` | Design notes: how `ifi account` picks a GitHub account without gh, and why the site runs as its own user `app` |
| `.devcontainer/docker-compose.devcontainer.yml` | Lets VS Code start the image instead of building it (the Docker Compose 5 "bake" fix) |
| `.vscode/tasks.json` | A "Restart Django server" task |
| `tools/ifi/` | The `ifi` commands (`ifi help` lists them): `check` (checks the whole setup; the first terminal runs a short version), `fix-issue`, `save` (add + commit, whole repo), `update` (catch up with `main`), `pull-request` (plain-language push errors, SSH → HTTPS), `undo-file` (take files out of a pull request), `cleanup` (merged branches), `account` (push as another GitHub account), `install` (`ifi` without Docker), `test`, `migrate`, `restart-server`, `reset-database`, `rebuild-docker`. They run in the container, on a Mac (bash 3.2) and in Git Bash on Windows |
| `tools/ifi/tests/` | ifi's own tests against a fake GitHub (`tools/ifi/tests/run`), a playground to try ifi by hand, and `manual_checklist.md` |
| `ifi`, `ifi.cmd` | Launchers in the repo root, for terminals outside the container (`ifi.cmd` for PowerShell, via Git Bash). Keep `ifi` executable |
| `.gitattributes` | Main's `* text=auto eol=lf`, plus `*.cmd text eol=crlf` (cmd.exe needs Windows line endings) |

**Replaces**
| File | Change |
| --- | --- |
| `README.md` | Quick start becomes "Get started" (2 steps, linking the new pages). New "Next steps" with the `ifi` flow, and a new docs list. Main's About is kept |
| `CONTRIBUTING.md` | Rewritten as numbered steps, with a GitHub Desktop table and a roles table. Main's Black/Pylint CI rules and the PR template are kept, and `ifi fix-issue`/`ifi pull-request` are mentioned |
| `TUTORIALS.md` | "Read these first" links and GitHub Desktop |
| `docs/README.md` | The new contributing pages are listed |
| `docs/contributing/setup_without_docker.md` | Step by step with explanations (venv, `.env`, the secret key), and `ifi` without Docker |
| `docs/contributing/everyday_commands.md` | Quick tests first, then the full suite |
| `docs/architecture/docker_setup.md` | initializeCommand, the restart loop, `ifi`, the bash terminal, the `.env.example` split, Norway's clock, and the `app` user |
| `docs/architecture/overview.md`, `frontend.md`, `ifi_home_app/events.md` | Tree diagrams become mermaid. Per-app diagrams in the overview. The overview's table notes where Docker keeps uploads and the cache |
| `docs/architecture/tech_stack.md` | Main's file, plus one sentence: the dev container keeps the cache in the database |
| `Dockerfile.dev` | bash as the shell, with completion. `procps`, `openssh-client`, `sudo`, the `ifi` link, `push.autoSetupRemote`. A second user `app` runs the site (see below). No GitHub CLI, on purpose |
| `docker-compose.yml` | `image: ifiplatform-web:dev`, runserver in a restart loop, `TZ=Europe/Oslo`, `user: app`, the `media` volume (`MEDIA_ROOT`), `CACHE_IN_DATABASE`, and `createcachetable` on start |
| `ifiplatform/ifiplatform_project/settings.py` | Main's file with two additions, both only active when the dev container sets their env var: `MEDIA_ROOT` from the env (with group-writable uploads), and a database cache with `CACHE_IN_DATABASE=True`. Production doesn't set either, so it's unchanged |
| `.devcontainer/devcontainer.json` | `initializeCommand` with plain `docker build` (Compose's bake fails on Windows), the override file, a bash terminal, the mermaid extension |
| `.vscode/extensions.json` | The mermaid extension |
| `ifiplatform/.env.example` | Split into "used everywhere" and "only without Docker" |

**The `app` user, in short.** The compose start command (`migrate`,
`seed_dev_data`, `runserver`) runs code from whatever branch is checked out,
by itself. It now runs as `app`, which can't read `/home/dev` (where the
Claude Code login is) or VS Code's login sockets. Terminals still open as
`dev`. Uploads go to a volume both can write to, and the cache moved into the
database, since a file cache only works for the user who wrote it.
`docker compose exec` now opens as `app`, so the docs say
`docker compose exec -u dev web bash`. Details:
`docs/claude_context/dev_container_users.md`.

## What was taken out

The event (sign-up and claiming on the mock site, coins and points,
helpers, `helpers.md`), `commits_app` (→ `yourpage_app`),
`seed_halloween_data` (→ `seed_dev_data` with `admin`/`admin`),
`rename_yourpage_app`, `OPEN_SIGNUP`, `GITHUB_READ_TOKEN`/`GITHUB_EVENT_REPO`,
the Files check (with its `files-reviewed` label and `Closes #` comment),
the event's PR template, `tblib` (only needed for the event's parallel CI
runs), and the event cut-down of CI (main still runs every test on
3.12–3.14, plus Black and Pylint). The "Protect Main" ruleset can't be used
while IfiPlatform is private on GitHub's free plan.

Changed from the Halloween version of ifi:
- `ifi pull-request` doesn't pre-fill `Closes #N`: a `body=` in the link
  would replace main's PR template. It reminds you to write the number on
  the template's `Closes #` line instead.
- `ifi undo-file` is kept. `undo-file <file>` works anywhere, and
  `--extra` only works for issues with a `### Files to change` list (without
  one, it says so).
- No pointers for old command names (`ifi status`, `ifi wipe-database`):
  IfiPlatform never had them.
- `MAIN_REPO="Creators-Guild/IfiPlatform"` in `tools/ifi/common.sh`. The
  tests read it from there.

## What ifi expects of IfiPlatform
- **Issue Types** `Bug`, `Feature`, `Task` (`fix-issue` names the branch
  `<type>/<few-words>`). Without Types it asks, which also works.
- **Merge commits**, not squash or rebase merging: `ifi cleanup` finds merged
  branches with `git branch --merged`. With squash merges it never finds any.
- **Branch protection**: `ifi` never pushes to main. It pushes to the
  student's branch, force only with a lease after `ifi update`.
- **`ifiplatform/`** as the Django folder with `manage.py`, and `apps/`
  without `__init__.py` (`ifi test`'s name checks).
- **The doc pages ifi links to**, all in this folder:
  `docs/contributing/get_the_code.md#log-in-to-github-once`,
  `docs/contributing/setup_without_docker.md`, and
  `docs/contributing/docker_guide.md#another-github-account-in-the-container`.

## Checked, and not checked yet

Checked in the Halloween repo (26 Oct):
- `tools/ifi/tests/run` passes, also when run from this folder with these
  changes (133 passed; `install` is skipped in the container).
- The quick Django tests pass there with the `app` user, the media volume and
  the database cache.
- These docs: link check, plus the links ifi prints. `settings.py` compiles.
- By hand there: runserver runs as `app`, `app` can't read the Claude login,
  and `ifi reset-database` works with the media volume.

**Not checked by hand anywhere yet:** `ifi account switch` on Windows, a Mac
and computers that log in with gh, uploads in the Wagtail admin with `app`,
and `./ifi` from outside the container. Nobody has opened the dev container
with these files inside IfiPlatform either.

**After copying, in IfiPlatform:**
1. `tools/ifi/tests/run`, and the project's own tests.
2. A fresh clone → Reopen in Container → the first terminal shows the setup check.
3. In the container: `id` lists group `app`; `ps -o user,cmd -C python`
   shows runserver as `app`; `sudo -u app cat /home/dev/.claude/.credentials.json`
   says Permission denied.
4. Log in as `admin`/`admin`, upload an image in the Wagtail admin, and run
   `ifi reset-database` (both write to `/srv/media`).
5. Part 1 of `tools/ifi/tests/manual_checklist.md` with a real issue,
   including the `ifi account` rows.

## Known limits (no Mac tester yet)
- `ifi install` on a Mac with zsh adds the alias, but not Tab completion.
- No `timeout` on a Mac, so `ifi check` can wait a long time offline.
- The `ifi` launcher uses `readlink -f`, which needs macOS 12.3 or newer.
