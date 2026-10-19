# Porting these files to IfiPlatform

The setup and onboarding docs from the Halloween repo, with the event parts
taken out, and the tooling they rely on. Every path here is the same path in
IfiPlatform, so you can copy the folder's contents over the repo root.

**Base:** these were made against IfiPlatform's `task/dockersetup-for-server`
(`c5fba9e`). The docs link to that branch's `docs/operations/docker_server.md`,
`Dockerfile` and `compose.prod.yml`, so apply them on top of it, or after it is
merged. Don't copy this `PORTING.md` itself.

## What to do in IfiPlatform

1. Copy everything except this file over the repo root.
2. Delete `docs/contributing/docker.md`. `docs/contributing/docker_guide.md` replaces it.
3. In `docs/operations/docker_server.md` (line 11), change the link
   `contributing/docker.md` to `contributing/docker_guide.md`.
4. Rebuild the dev container, which is needed for the new `Dockerfile.dev`.

## Files

**New**
| File | What it is |
| --- | --- |
| `docs/contributing/get_the_code.md` | Fork (contributors) or clone (collaborators), logging in to GitHub, GitHub Desktop |
| `docs/contributing/setup_with_docker.md` | First-time Docker setup (was the README's Quick start) |
| `docs/contributing/docker_guide.md` | Replaces `docker.md`: how Docker works here, restart/rebuild/reset, `.env`, problems |
| `docs/contributing/how_this_project_works.md` | Beginner's map: Django in plain words, folders, "where do I change…?" |
| `docs/contributing/collaborators.md` | The same steps with `origin` instead of `upstream` |
| `docs/contributing/images/*.svg` | The fork and clone diagrams |
| `.devcontainer/docker-compose.devcontainer.yml` | Lets VS Code start the image instead of building it (the Docker Compose 5 "bake" fix) |
| `.vscode/tasks.json` | A "Restart Django server" task |
| `tools/ifi/` | The `ifi` commands (`ifi help` lists them): `status` (checks the whole setup), `fix-issue`, `save` (add + commit, whole repo), `update` (catch up with `main`), `pull-request` (plain-language push errors, SSH → HTTPS), `cleanup` (merged branches), `install` (`ifi` without Docker), `test`, `migrate`, `restart-server`, `reset-server`, `rebuild-docker`. They run in the container, on a Mac (bash 3.2) and in Git Bash on Windows |
| `ifi`, `ifi.cmd` | Launchers in the repo root, for terminals outside the container (`ifi.cmd` for PowerShell, via Git Bash). Keep `ifi` executable |
| `.gitattributes` | Main's `* text=auto eol=lf`, plus `*.cmd text eol=crlf` (cmd.exe needs Windows line endings) |

**Replaces**
| File | Change |
| --- | --- |
| `README.md` | Quick start becomes "Get started" (2 steps, linking the new pages). New "Next steps" with the `ifi` flow, and a new docs list. Main's About is kept |
| `CONTRIBUTING.md` | Rewritten as numbered steps, with a GitHub Desktop table and a roles table. Main's Black/Pylint CI rules and the PR template are kept, and `ifi fix-issue`/`ifi pull-request` are mentioned |
| `TUTORIALS.md` | "Read these first" links and GitHub Desktop |
| `docs/README.md` | The new contributing pages are listed |
| `docs/contributing/setup_without_docker.md` | Step by step with explanations (venv, `.env`, the secret key) |
| `docs/contributing/everyday_commands.md` | Quick tests first, then the full suite |
| `docs/architecture/docker_setup.md` | initializeCommand, the restart loop, `ifi`, the bash terminal, the `.env.example` split |
| `docs/architecture/overview.md`, `frontend.md`, `ifi_home_app/events.md` | Tree diagrams become mermaid. Per-app diagrams in the overview |
| `Dockerfile.dev` | bash as the shell, with completion. `procps`, `openssh-client`, the `ifi` link, `push.autoSetupRemote` |
| `docker-compose.yml` | `image: ifiplatform-web:dev`, and runserver in a restart loop |
| `.devcontainer/devcontainer.json` | `initializeCommand` with plain `docker build` (Compose's bake fails on Windows), the override file, a bash terminal, the mermaid extension |
| `.vscode/extensions.json` | The mermaid extension |
| `ifiplatform/.env.example` | Split into "used everywhere" and "only without Docker" |

## What was taken out

The event (sign-up and claiming on the mock site, coins and points,
helpers, `helpers.md`), `commits_app` (→ `yourpage_app`),
`seed_halloween_data` (→ `seed_dev_data` with `admin`/`admin`),
`rename_yourpage_app`, `OPEN_SIGNUP`, `GITHUB_READ_TOKEN`/`GITHUB_EVENT_REPO`,
`ifi undo-file` and the Files check (with its `files-reviewed` label and
`Closes #` comment), the event's PR template, `tblib` (only needed for the
event's parallel CI runs), and the event cut-down of CI (main still runs
every test on 3.12–3.14, plus Black and Pylint). The "Protect Main" ruleset
can't be used while IfiPlatform is private on GitHub's free plan. `ifi pull-request` no
longer pre-fills `Closes #N`, so main's PR template shows. It reminds you to
add the issue number instead.

## Not checked yet

The docs and scripts were checked by reading and by syntax checks
(`bash -n`, `docker compose config`, link check). Nobody has opened the dev
container with these files inside IfiPlatform yet. The `ifi` commands
themselves were tested in the Halloween repo (including bash 3.2 and the
launchers). After copying: Reopen in Container, check the `(container)`
prompt, try `ifi status`, `ifi test` and `ifi restart-server`, and log in as
`admin`/`admin`.
