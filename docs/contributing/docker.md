# Working with the Docker setup

Last updated: 2026-10-11

Day-to-day use of the Docker setup: extensions, running it without VS Code,
stopping and resetting, and fixing problems. To start it the first time, see
the quick start in the main [README.md](../../README.md#quick-start). How it's
built and why: [architecture/docker_setup.md](../architecture/docker_setup.md).

## Adding your own VS Code extensions
The container comes with the extensions this project needs (Python, Black, Pylint and Django templates). Themes and keyboard shortcuts you already have keep working. Other extensions (for example Claude Code or GitHub Copilot) have to be installed inside the container, and ones you install by hand disappear when the container is rebuilt.

To get them in every container automatically, add them to your own VS Code settings (Command Palette → `Preferences: Open User Settings (JSON)`):
```json
"dev.containers.defaultExtensions": ["anthropic.claude-code"]
```
Each extension's ID is shown as "Identifier" on its page in the Extensions view. Claude Code stays logged in when the container is rebuilt.

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
- **The site stopped or won't load after a code error:** the error is in the log (`docker compose logs web`). Fix it, then start the server again in the container terminal with `python manage.py runserver 0.0.0.0:8000`. If the error came from a migration, run `python manage.py migrate` first. The container keeps running while the server is stopped, so the terminal still works. Next time the container starts, the server starts by itself again.
- **`ModuleNotFoundError` after pulling or switching branches:** someone added a package to `requirements.txt`, and your container doesn't have it yet. Run `Dev Containers: Rebuild Container` from the Command Palette (without VS Code: `docker compose up -d --build`).
- **Docker Desktop won't start (Windows):** it needs WSL2 and virtualization. Run `wsl --install` in PowerShell as administrator and restart. If Docker still complains, turn on virtualization in your computer's BIOS/UEFI settings (called "Intel VT-x", "AMD-V" or "SVM"). Docker Desktop's error message usually says which one is missing.
- **Everything is slow (Windows):** projects cloned to a Windows drive like `C:\` are slow in Docker. It's much faster to clone inside WSL: open the Ubuntu terminal, clone the repo there, run `code .` in the repo folder, then click "Reopen in Container".
- **Docker is too slow or won't install:** use the [setup without Docker](setup_without_docker.md) instead.

The Docker database is also reachable from your own computer at `localhost:5433`, for example from a database tool (user `ifiplatform_user`, password `devpassword`).
