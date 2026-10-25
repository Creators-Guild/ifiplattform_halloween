# Moving ifi and the Docker setup to the main ifiplattform

Last updated: 2026-10-26

The mock repo (ifiplattform_halloween) is where the onboarding tooling was
built and tested. Two parts move to the main repo: **ifi** and the
**Docker / VS Code setup**. The contributor docs and the Commit for Candy
event checks stay here. Delete this plan when the move is done.

How to work: open the main repo (`Creators-Guild/ifiplattform`) in its own
folder, next to this one, and copy files over from here. If main has no dev
container yet, the first session runs on the computer itself.

## Before: test here
- `tools/ifi/tests/run`: everything passes (in the container; `install` is skipped there).
  Done 2026-10-26: 135 passed, and `ifi test`: 345 passed.
- `tools/ifi/tests/manual_checklist.md`: **skipped** (the user's choice,
  2026-10-26). Not checked by hand yet: `ifi account switch` on Windows,
  Mac and gh computers, uploads and `ifi reset-database` with the `app`
  user, and `./ifi` from outside the container. Do part 1 in main instead
  (see "After").

## What moves

| Files | Notes |
| --- | --- |
| `tools/ifi/` (with `pages/` and `tests/`) | All of it |
| `ifi`, `ifi.cmd` (repo root) | Launchers for outside the container |
| `.gitattributes` | `*.cmd text eol=crlf`, or `ifi.cmd` breaks in cmd.exe |
| `Dockerfile.dev` | Links `ifi` into the PATH, loads `shell-setup.sh`, openssh-client, `push.autoSetupRemote` |
| `.devcontainer/devcontainer.json` + `docker-compose.devcontainer.yml` | Ports: `portsAttributes` / `otherPortsAttributes`, no `forwardPorts` (Docker already publishes 8000) |
| `docker-compose.yml` | The runserver loop `ifi restart-server` relies on, and `init: true`. Also `user: app`, the `media` volume (`MEDIA_ROOT`), `CACHE_IN_DATABASE`, `createcachetable`, the one-time media copy and the `chmod` step. No `gh-config` volume |
| `Dockerfile.dev`, more | No gh. The `app` user, `sudo` (dev may act as app only), dev in app's group, `/srv/media` (2775), `chmod 700 /home/dev` |
| `ifiplatform/ifiplatform_project/settings.py` (parts) | Port by hand, since main's settings differ: `MEDIA_ROOT` from the env, `FILE_UPLOAD_*_PERMISSIONS` when it's set, and the `CACHE_IN_DATABASE` block (before the test runner's LocMem override). Prod must stay unchanged without these env vars |
| `docs/claude_context/ifi_account.md`, `dev_container_users.md` | If main has `docs/claude_context/`. Their `Covers:` paths stay the same |

Keep the Git file mode: every script in `tools/ifi/` and `ifi` must be
`100755` (the test `commands_are_executable_in_git` checks it).

## What doesn't move
- `testchange` (repo root): an empty leftover from the "test" commit. Deleted here.
- The event checks: `.github/workflows/files_check.yml`, the "points" text
  in `.github/pull_request_template.md`, and the CI lines marked `EVENT`.
- `tblib` in `requirements.txt`: only needed for the event CI's
  `manage.py test --parallel`. Take it only if main tests in parallel.
- The Halloween seed and the `rename_yourpage_app` command.
- The `status)` and `wipe-database)` cases in `tools/ifi/ifi`, and
  `wipe-database` in the root `ifi` launcher's case list: old names. Main
  never had ifi, so nobody there needs the pointers. Drop their tests too
  (`commands_old_status_name_points_to_check`,
  `commands_old_wipe_database_name_points_to_reset_database`).

## Mock-only names to change

| Where | Now | In main |
| --- | --- | --- |
| `tools/ifi/common.sh` | `MAIN_REPO="Creators-Guild/ifiplattform_halloween"` | `Creators-Guild/ifiplattform`. The tests read it from here |
| `tools/ifi/check` (the "not in the project" line) | `ifiplattform_halloween folder` | main's folder name |
| `tools/ifi/check` (the "Nothing needs a look" line) | `Nothing needs a look. All good. 🎃` | without the 🎃 |
| `devcontainer.json` (`initializeCommand`), `docker-compose.yml` (`image`), `tools/ifi/rebuild-docker` (twice) | `ifiplattform-halloween-web:dev` | one new name, the same in all three |
| `devcontainer.json` | `"name": "IfiPlatform Halloween"` | `IfiPlatform` |
| `docker-compose.yml` | `container_name: halloween-db`, `halloween-web` | new names, so both repos' containers can exist side by side |
| `docker-compose.yml` command, `tools/ifi/reset-database` | `rename_yourpage_app`, `seed_halloween_data` | main's seed command (and no rename step) |
| `docker-compose.yml` | `OPEN_SIGNUP` comment about the mock site | check main's sign-up |
| `tools/ifi/test` comment | `apps.halloween_app.tests` | an app main has |

## What ifi expects of main
- **Doc pages it prints links to.** The contributor docs don't move, so
  these must exist in main (or the links in ifi must change):
  `docs/contributing/get_the_code.md#log-in-to-github-once`
  (`common.sh`, `check`), `docs/contributing/setup_without_docker.md`
  (`common.sh`) and
  `docs/contributing/docker_guide.md#another-github-account-in-the-container`
  (`explain_account_login` in `common.sh`). The Docker guide's "Another
  GitHub account" and "Your Claude Code login" sections and docker_setup.md's
  `app` bullet explain the new setup. Bring those parts along if main has
  matching docs.
- **`docker compose exec -u dev`** wherever main's docs say `docker compose exec web ...`
  (the container's default user is now `app`).
- **Issue Types** `Bug`, `Feature`, `Task` (`fix-issue` names the branch
  `<type>/<few-words>`). Without Types it asks, which also works.
- **Merge commits**, not squash or rebase merging: `ifi cleanup` finds merged
  branches with `git branch --merged`. With squash merges it never finds any.
- **`### Files to change`** in issues: only for `ifi undo-file --extra`.
  Without it, `undo-file <file>` still works.
- **Branch protection**: `ifi` never pushes to main. It pushes to the
  student's branch, force only with a lease after `ifi update`.
- **`ifiplatform/`** as the Django folder with `manage.py`, `apps/` without
  `__init__.py` (`ifi test`'s name checks).

## After: check in main
1. `tools/ifi/tests/run` passes there, and main's own test suite.
2. A fresh clone → Reopen in Container → the first terminal shows the setup check.
3. In the container: `id` lists group `app`, `ps -o user,cmd -C python` shows
   runserver as `app`, and `sudo -u app cat /home/dev/.claude/.credentials.json`
   says Permission denied.
4. Upload an image in the Wagtail admin, and run main's seed/reset command
   (both write `/srv/media`).
5. Part 1 of `manual_checklist.md` with a real issue in main, including the
   `ifi account` rows.

## Known limits (no Mac tester yet)
- `ifi install` on a Mac with zsh adds the alias, but not Tab completion.
- No `timeout` on a Mac, so `ifi check` can wait a long time offline.
- The `ifi` launcher uses `readlink -f`, which needs macOS 12.3 or newer.
