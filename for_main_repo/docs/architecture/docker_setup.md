# Docker setup

Last updated: 2026-10-26

How the local Docker setup is built and why. To start it, see
[contributing/setup_with_docker.md](../contributing/setup_with_docker.md). For day-to-day
use and troubleshooting, see
[contributing/docker_guide.md](../contributing/docker_guide.md). It is for local
development only. Servers use a separate Docker setup (`Dockerfile`,
`compose.prod.yml`), described in
[operations/docker_server.md](../operations/docker_server.md). The real
site still runs without Docker until it moves over (see
[operations/server_setup.md](../operations/server_setup.md)).

## Files

| File                              | What it does                                               |
| --------------------------------- | ---------------------------------------------------------- |
| `Dockerfile.dev`                  | Builds the Django container: Python 3.12, the packages from `requirements.txt`, and the `ifi` command (a link to `tools/ifi/ifi`) |
| `docker-compose.yml`              | Runs two containers: `db` (PostgreSQL 16) and `web` (Django) |
| `.devcontainer/devcontainer.json` | Lets VS Code open the `web` container ("Reopen in Container"). Builds the image first (`initializeCommand`), shows the whole repo, starts new terminals in `ifiplatform/`, and installs the editor extensions (see below) |
| `.devcontainer/docker-compose.devcontainer.yml` | Used only by VS Code, on top of `docker-compose.yml`. Hides `build`, so VS Code starts the already built image instead of building it (see below) |
| `.vscode/settings.json`, `.vscode/extensions.json` | Editor settings and recommended extensions. Used both in the container and without Docker |
| `tools/ifi/`                      | Our own `ifi` commands (`ifi help` lists them). Shared into the container with the rest of the repo, so editing them needs no rebuild. `shell-setup.sh` adds Tab completion, the `(container)` prompt and, in the first terminal after the container starts, `ifi check --quiet` (later terminals show the latest result instead, saved in `/dev/shm`), loaded from the dev user's `.bashrc`. The scripts also run without Docker (bash 3.2 on a Mac, Git Bash on Windows) |
| `ifi`, `ifi.cmd` (repo root)      | Launchers for terminals outside the container (`.cmd` for PowerShell, via Git Bash). Commands that need the site's Python go into the running container; Git commands stay on your computer, where the GitHub login is |
| `.dockerignore`                   | Keeps the venv, local database, media and `.env` out of the build |

## What happens on start

0. Before VS Code does anything, `initializeCommand` runs
   `docker build -f Dockerfile.dev -t ifiplatform-web:dev .` on
   your own computer. It builds
   `Dockerfile.dev` into the image `ifiplatform-web:dev`. After
   the first time Docker's cache makes this take a second or two.
1. `db` starts. `web` waits until the database answers (the healthcheck).
2. `web` runs `migrate`, then `seed_dev_data`, then `runserver` in
   a loop: whenever the server stops, it starts again after 2 seconds.
   `seed_dev_data` skips what already exists, so it's safe to run on
   every start. It also creates the `admin` / `admin` superuser.
3. The site is served at `localhost:8000`.
4. If `migrate` or the seeding fails, the container keeps running
   (`sleep infinity`). Without that, a broken migration would stop the
   container on every start, and VS Code couldn't reopen it to fix the
   error. The student fixes the error and runs `ifi restart-server`.
5. `ifi restart-server` (a small script in `tools/ifi/`) stops the
   running server, and the loop starts a fresh one. A fresh process is
   needed for things `runserver`'s own reload misses, like a new
   `templatetags` file. It matches only the Python processes, not the
   loop's `sh -c` line, which also contains "manage.py runserver". With
   no server running, it runs `migrate` and starts one in the terminal.

The repo is shared into the container at `/workspace`, so file edits on
your own computer show up right away and `runserver` reloads.

## Why it's built this way

- **VS Code doesn't build the image.** When the Dev Containers extension
  builds a Compose service, it adds its own Dockerfile from a temporary
  folder outside the project. Docker Compose 5.x builds with "bake",
  which refuses to read files outside the project, so the build stopped
  at once with `additional privileges requested: pass --allow=fs.read=...`
  (seen on a Mac with Docker Desktop 4.95 in October 2026). So
  `initializeCommand` builds the image itself. It uses plain
  `docker build`, not `docker compose build`, because Compose hands every
  build to bake, and on Windows bake failed even on our own
  `Dockerfile.dev` (`--allow=fs.read=Dockerfile.dev` or
  `failed to execute bake`, Docker Desktop 4.95 and 4.96, October 2026).
  Plain `docker build` never uses bake. The image name must match
  `image:` in `docker-compose.yml`. The override
  `.devcontainer/docker-compose.devcontainer.yml` then removes `build`
  (`!reset`, which needs Compose 2.24 or newer), so the extension starts
  that image instead. `pull_policy: never` stops Compose from looking for
  the local image name on Docker Hub if the build failed. Outside VS Code,
  `docker compose up --build` still builds through Compose, so on Windows
  it can hit the same bake error (see the
  [Docker guide](../contributing/docker_guide.md#if-something-goes-wrong)).
- **Commands stay the same.** Students work inside the container
  (VS Code's terminal, or `docker compose exec -u dev web bash`), so the
  README's `python manage.py ...` commands work unchanged. `py` is
  linked to `python` in the container, so the Windows style works too.
- **No `.env` needed to run the site.** `web` sets every needed setting in
  `docker-compose.yml`. A student's own `ifiplatform/.env` can't override
  them, because python-dotenv never replaces a variable that is already
  set. The same `.env` keeps working with SQLite outside Docker.
  `.env.example` is split to match: part 1 (keys like
  `DEEPL_API_KEY`) is read in Docker too, part 2 is only for running
  without Docker.
- **Norway's clock.** `docker-compose.yml` sets `TZ=Europe/Oslo`, so the
  terminal, Git commits and `ifi check` show Norwegian time, with summer
  and winter time, instead of UTC. The site isn't affected: Django uses
  `TIME_ZONE` from its settings.
- **Same versions as production:** Python 3.12 and PostgreSQL 16. CI
  also runs the tests on PostgreSQL 16, so a test that passes in the
  container passes in CI.
- **Ports only on your own computer.** Both ports are bound to
  `127.0.0.1`, so nobody else on the network (like event Wi-Fi) can reach
  the site with its `admin`/`admin` user, or the database.
- **Database on port 5433, not 5432,** so it doesn't clash with a
  PostgreSQL the student already has installed.
- **Start commands are written inline in `docker-compose.yml`,** not in a
  `.sh` script, so the whole setup is readable in one file.
- **Line endings are always LF.** `.gitattributes` makes Git check out
  every file with LF, even on Windows. Without it, Git on Windows turns
  files into CRLF, and Git inside the Linux container then sees every file
  as changed (and shell scripts break).
- **The terminal is bash, with completion.** Debian's default shell for a
  new user is sh (dash), which has no Tab completion or arrow-key history,
  so `Dockerfile.dev` creates the `dev` user with `--shell /bin/bash` and
  installs `bash-completion`. `devcontainer.json` also sets bash as VS
  Code's default terminal.
- **Editor tools come with the container.** The Python, Black, Pylint,
  Django template and Markdown Mermaid extensions are installed automatically. Pylint uses the
  same plugin and settings module as CI, so the editor underlines what CI
  would complain about. Black formats Python files on save. The whole
  codebase was formatted once, so saving only changes the lines you
  edited.
- **Editor settings live in `.vscode/`, not in `devcontainer.json`,** so
  students who don't use Docker get the same setup. VS Code offers to
  install the extensions from `.vscode/extensions.json`. The container
  ignores those recommendations, so the same list is also in
  `devcontainer.json`. Add a new extension to both.
- **A normal user, not root.** The container runs as the user `dev`.
  Files made inside it, like new migrations, land in the shared folder on
  the student's computer. On Linux they'd be owned by root if the
  container ran as root, and the student couldn't edit them without
  `sudo`. VS Code changes `dev`'s user ID to match the student's own when
  the container starts, so the files belong to them. Without VS Code
  (`docker compose up`), `dev` keeps ID 1000, which is the usual ID of
  the first user on a Linux computer. Docker Desktop (Windows and macOS)
  hides this problem either way.
- **The site runs as its own user, `app`.** VS Code's terminals open as
  `dev`, but the server and the start-up steps run as `app`. Those steps
  run code from whatever branch is checked out, so they could otherwise
  read `dev`'s logins, like Claude Code's. `app` can read the project but
  not `/home/dev`. Because `app` can't write to the shared folder,
  uploads go to the `media` volume (`MEDIA_ROOT=/srv/media`). The first
  start copies any old `ifiplatform/media` into it. The cache is a table
  in the database (`CACHE_IN_DATABASE`), since a file cache only works
  for the user who wrote it. `dev` may run commands as `app` with
  `sudo -u app` (`ifi restart-server` does), but `app` can't become
  anyone else. `docker compose exec` opens as `app`, so use
  `docker compose exec -u dev web bash`.
- **Claude Code stays logged in.** Its login and settings are kept in the
  `claude-config` volume (`CLAUDE_CONFIG_DIR`), so they survive rebuilds
  and `docker compose down`. Only `down -v` deletes them. Shared Claude
  Code permissions (safe commands like running the tests) are in
  `.claude/settings.json`. Personal ones go in
  `.claude/settings.local.json`, which Git ignores. The extension
  isn't installed for everyone; students who want it add it themselves
  (see [contributing/docker_guide.md](../contributing/docker_guide.md)).
- **Code isn't copied into the image.** It's shared in instead, so the image
  only needs rebuilding when `requirements.txt` changes.

## Security

The password (`devpassword`) and secret key in `docker-compose.yml` are
fake and only for local use. Never reuse them on a server.
