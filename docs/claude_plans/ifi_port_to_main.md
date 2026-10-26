# Moving ifi and the Docker setup to the main ifiplattform

Last updated: 2026-10-26

The mock repo (ifiplattform_halloween) is where the onboarding tooling was
built and tested. Two parts move to the main repo: **ifi** and the
**Docker / VS Code setup**. The contributor docs and the Commit for Candy
event checks stay here. Delete this plan when the move is done.

## Before: test here
- `tools/ifi/tests/run`: everything passes (in the container; `install` is skipped there).
- `tools/ifi/tests/manual_checklist.md`: Linux and Windows done.

## What moves

| Files | Notes |
| --- | --- |
| `tools/ifi/` (with `pages/` and `tests/`) | All of it |
| `ifi`, `ifi.cmd` (repo root) | Launchers for outside the container |
| `.gitattributes` | `*.cmd text eol=crlf`, or `ifi.cmd` breaks in cmd.exe |
| `Dockerfile.dev` | Links `ifi` into the PATH, loads `shell-setup.sh`, openssh-client, `push.autoSetupRemote` |
| `.devcontainer/devcontainer.json` + `docker-compose.devcontainer.yml` | Ports: `portsAttributes` / `otherPortsAttributes`, no `forwardPorts` (Docker already publishes 8000) |
| `docker-compose.yml` | The runserver loop `ifi restart-server` relies on, and `init: true` |

Keep the Git file mode: every script in `tools/ifi/` and `ifi` must be
`100755` (the test `commands_are_executable_in_git` checks it).

## What doesn't move
- `testchange` (repo root): an empty leftover from the "test" commit. Deleted here.
- The event checks: `.github/workflows/files_check.yml`, the "points" text
  in `.github/pull_request_template.md`, and the CI lines marked `EVENT`.
- `tblib` in `requirements.txt`: only needed for the event CI's
  `manage.py test --parallel`. Take it only if main tests in parallel.
- The Halloween seed and the `rename_yourpage_app` command.
- The `status)` case in `tools/ifi/ifi`: the old name of `ifi check`.
  Main never had `ifi status`, so nobody there needs the pointer.

## Mock-only names to change

| Where | Now | In main |
| --- | --- | --- |
| `tools/ifi/common.sh` | `MAIN_REPO="Creators-Guild/ifiplattform_halloween"` | main's owner/name. The tests read it from here |
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
  (`common.sh`, `status`) and `docs/contributing/setup_without_docker.md`
  (`common.sh`).
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
1. `tools/ifi/tests/run` passes there.
2. A fresh clone → Reopen in Container → the first terminal shows the setup check.
3. Part 1 of `manual_checklist.md` with a real issue in main.

## Known limits (no Mac tester yet)
- `ifi install` on a Mac with zsh adds the alias, but not Tab completion.
- No `timeout` on a Mac, so `ifi check` can wait a long time offline.
- The `ifi` launcher uses `readlink -f`, which needs macOS 12.3 or newer.
