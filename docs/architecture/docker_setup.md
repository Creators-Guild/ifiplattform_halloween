# Docker setup

Last updated: 2026-10-14

How the local Docker setup is built and why. To start it, see the Quick
start in the main [README.md](../../README.md#quick-start). For day-to-day
use and troubleshooting, see
[contributing/docker.md](../contributing/docker.md). It is for local
development only. Servers use a separate Docker setup (`Dockerfile`,
`compose.prod.yml`), described in
[operations/docker_server.md](../operations/docker_server.md). The real
site still runs without Docker until it moves over (see
[operations/server_setup.md](../operations/server_setup.md)).

## Files

| File                              | What it does                                               |
| --------------------------------- | ---------------------------------------------------------- |
| `Dockerfile.dev`                  | Builds the Django container: Python 3.12 and the packages from `requirements.txt` |
| `docker-compose.yml`              | Runs two containers: `db` (PostgreSQL 16) and `web` (Django) |
| `.devcontainer/devcontainer.json` | Lets VS Code open the `web` container ("Reopen in Container"). Shows the whole repo; new terminals start in `ifiplatform/`. Installs the editor extensions (see below) |
| `.vscode/settings.json`, `.vscode/extensions.json` | Editor settings and recommended extensions. Used both in the container and without Docker |
| `.dockerignore`                   | Keeps the venv, local database, media and `.env` out of the build |

## What happens on start

1. `db` starts. `web` waits until the database answers (the healthcheck).
2. `web` runs `migrate`, then `seed_dev_data`, then `runserver`.
   `seed_dev_data` skips what already exists, so it's safe to run on
   every start.
3. The site is served at `localhost:8000`.
4. If any of these steps fails or the server stops, the container keeps
   running (`sleep infinity`). Without that, a broken migration or a typo
   in `settings.py` would stop the container on every start, and VS Code
   couldn't reopen it to fix the error. The student fixes the error and
   runs `runserver` again in the terminal.

The repo is shared into the container at `/workspace`, so file edits on
your own computer show up right away and `runserver` reloads.

## Why it's built this way

- **Commands stay the same.** Students work inside the container
  (VS Code's terminal, or `docker compose exec web bash`), so the
  README's `python manage.py ...` commands work unchanged. `py` is
  linked to `python` in the container, so the Windows style works too.
- **No `.env` needed.** `web` sets every needed setting in
  `docker-compose.yml`. A student's own `ifiplatform/.env` can't override
  them, because python-dotenv never replaces a variable that is already
  set. The same `.env` keeps working with SQLite outside Docker.
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
- **Editor tools come with the container.** The Python, Black, Pylint and
  Django template extensions are installed automatically. Pylint uses the
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
- **Claude Code stays logged in.** Its login and settings are kept in the
  `claude-config` volume (`CLAUDE_CONFIG_DIR`), so they survive rebuilds
  and `docker compose down`. Only `down -v` deletes them. Shared Claude
  Code permissions (safe commands like running the tests) are in
  `.claude/settings.json`. Personal ones go in
  `.claude/settings.local.json`, which Git ignores. The extension
  isn't installed for everyone; students who want it add it themselves
  (see [contributing/docker.md](../contributing/docker.md)).
- **Code isn't copied into the image.** It's shared in instead, so the image
  only needs rebuilding when `requirements.txt` changes.

## Security

The password (`devpassword`) and secret key in `docker-compose.yml` are
fake and only for local use. Never reuse them on a server.
