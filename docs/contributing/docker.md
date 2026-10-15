# Working with the Docker setup

Last updated: 2026-10-15

Day-to-day use of the Docker setup: extensions, running it without VS Code,
stopping and resetting, and fixing problems. To start it the first time, see
[setup_with_docker.md](setup_with_docker.md). New to Docker? Read
[Docker, explained simply](docker_explained.md). How it's
built and why: [architecture/docker_setup.md](../architecture/docker_setup.md).

## Adding your own VS Code extensions
The container comes with the extensions this project needs (Python, Black, Pylint, Django templates, and Mermaid diagrams in the Markdown preview). Themes and keyboard shortcuts you already have keep working. Other extensions (for example Claude Code or GitHub Copilot) have to be installed inside the container, and ones you install by hand disappear when the container is rebuilt.

To get them in every container automatically, add them to your own VS Code settings (Command Palette → `Preferences: Open User Settings (JSON)`):
```json
"dev.containers.defaultExtensions": ["anthropic.claude-code"]
```
Each extension's ID is shown as "Identifier" on its page in the Extensions view. Claude Code stays logged in when the container is rebuilt.

## Keys and tokens (.env)
The site runs without a `.env` file. You only need one for extra features, like the GitHub token that updates the event points. Copy the example and fill in what you need from its first part:
```bash
cp .env.example .env
```
Part 2 of the file ("Only without Docker") does nothing in the container, because `docker-compose.yml` already sets those settings. You can leave it or delete it. After changing `.env`, run `restart-server`.

## Without VS Code
Run these from the repo root in any terminal:
```bash
docker compose up -d
```
Builds and starts everything in the background. The site is ready at http://localhost:8000 after a minute.
```bash
docker compose exec web bash
```
Opens a terminal inside the container. From there, every `python manage.py ...` command works as normal. Type `exit` to leave.

## Stopping and resetting
```bash
docker compose down
```
Stops everything. Your database is kept for next time.
```bash
docker compose down -v
```
Stops everything **and deletes the database**. Next start gives you a fresh database with new test data. It also logs you out of Claude Code, if you use it.
```bash
docker compose up -d --build
```
Rebuilds the container. Only needed after `requirements.txt` or the Docker files change. In VS Code: Command Palette → `Dev Containers: Rebuild Container`.

## If something goes wrong
- **"Port 8000 is already in use":** another `runserver` is running on your computer. Stop it (Ctrl+C in its terminal) and try again.
- **See what the container is doing:** `docker compose logs -f web`. Press Ctrl+C to stop watching.
- **Restart the server:** run `restart-server` in the container terminal (or Command Palette → `Tasks: Run Task` → `Restart Django server`). The server restarts by itself when you save a file, but it only picks up some things when it starts: a new `templatetags` file ("is not a registered tag library"), or a new setting in `ifiplatform/.env` (settings that `docker-compose.yml` sets can't be changed in `.env` at all).
- **The site stopped or won't load after a code error:** the error is in the log (`docker compose logs web`). Fix it and the server comes back by itself within a few seconds; if it doesn't, run `restart-server`. If start-up failed (for example a broken migration), `restart-server` runs `migrate` and starts the server in your terminal. The container keeps running while the server is stopped, so the terminal still works. If `restart-server` isn't found, your container is older than this command: run `Dev Containers: Rebuild Container`.
- **`ModuleNotFoundError` after pulling or switching branches:** someone added a package to `requirements.txt`, and your container doesn't have it yet. Run `Dev Containers: Rebuild Container` from the Command Palette (without VS Code: `docker compose up -d --build`).
- **Docker Desktop won't start (Windows):** it needs WSL2 and virtualization. Run `wsl --install` in PowerShell as administrator and restart. If Docker still complains, turn on virtualization in your computer's BIOS/UEFI settings (called "Intel VT-x", "AMD-V" or "SVM"). Docker Desktop's error message usually says which one is missing.
- **Everything is slow (Windows):** projects cloned to a Windows drive like `C:\` are slow in Docker. It's much faster to clone inside WSL: open the Ubuntu terminal, clone the repo there, run `code .` in the repo folder, then click "Reopen in Container".
- **Docker is too slow or won't install:** use the [setup without Docker](setup_without_docker.md) instead.

The Docker database is also reachable from your own computer at `localhost:5433`, for example from a database tool (user `ifiplatform_user`, password `devpassword`).
