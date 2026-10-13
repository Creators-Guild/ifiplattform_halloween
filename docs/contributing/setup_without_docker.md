# Setup without Docker (Python + SQLite)

Last updated: 2026-10-11

Only use this if Docker is too heavy for your laptop or won't install. The
recommended setup is Docker, see the quick start in the main
[README.md](../../README.md#quick-start).

## Requirements
- Python 3.12 or newer (tested on 3.12, 3.13 and 3.14)
- SQLite, which comes with Python

> **A note on file paths below:** "repo root" means the top-level folder you get from cloning (likely named `IfiPlatform`). 

>Steps also reference the `ifiplatform/` subdirectory inside it (likely named `ifiplatform`, lowercase (*not to be confused with `ifiplatform/ifiplatform_project/`, which is just the Django settings package*) — that's where manage.py, `.env` and all the Django apps actually live. Steps say which one they're relative to.

## 0. Fork and clone
Follow item 1 under "2. Open the project in the container" in the README's [Quick start](../../README.md#quick-start): fork the repo, clone your fork and add the `upstream` remote. Skip the rest of the Quick start, which is for Docker.

## 1. Set up Virtual Environment
### Windows (PowerShell)
```bash
py -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell says running scripts is disabled, run this once and try again:
```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```
### Or through Visual Studio Code
Run this command from the Command Palette:
```bash
Python: Create Environment
```
## 2. Install dependencies
Run from the repo root:
```bash
pip install -r requirements.txt
```
In VS Code, click **Install** when it offers the project's recommended extensions (Python, Black, Pylint and Django templates). Then pick your venv with Command Palette → `Python: Select Interpreter`, so the editor uses the same Black and pylint versions as everyone else. Black formats Python files when you save, just like in Docker.

## 3. Move into the ifiplatform/ folder
manage.py, `.env` and all the Django apps live in `ifiplatform/`. Every command from here on assumes you're inside it:
```bash
cd ifiplatform
```

## 4. Create .env for Secrets
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
That's enough for local development: the placeholder secret key works on your own computer, and you can ignore the rest of the file. (Any server needs a real random key. This prints one:)
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
If you skip this step, Django stops with an error saying `DJANGO_SECRET_KEY is not set`.

## 5. Run Migrations
```bash
python manage.py migrate
```

## 6. Fill database with dummy data(recommended)
```bash
python manage.py seed_dev_data
```
Fills your local database with a dummy article tree (index pages, categories, a test article, a test student union and a test tool) so you're not starting from a blank site. Safe to re-run — it skips anything that already exists instead of duplicating it.

## 7. Run website on localhost
```bash
python manage.py runserver
```
Once running, open your browser and go to:
```
http://localhost:8000
```

### Access from your phone (same Wi-Fi)
Useful for testing responsive/mobile layout on a real device. This only works with this setup: the Docker setup only accepts connections from your own computer.

1. Start the server bound to all network interfaces, not just localhost:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
2. Find your computer's local IP address:
   - **Windows:** run `ipconfig` in a terminal, look for `IPv4 Address` under your active adapter (e.g. `192.168.1.23`)
   - **macOS:** `ipconfig getifaddr en0` (or check System Settings → Wi-Fi → Details)
   - **Linux:** `hostname -I` or `ip addr`
3. Add that IP to `DJANGO_ALLOWED_HOSTS` in your `.env` (comma-separated, no spaces), then restart the server:
   ```
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.23
   ```
   Without this, Django rejects the request with a 400 `DisallowedHost` error — `ALLOWED_HOSTS` is read straight from this env var (`settings.py`), it isn't relaxed just because `DEBUG=True`.
4. On your phone, connected to the **same Wi-Fi network**, open:
   ```
   http://192.168.1.23:8000
   ```
   (use your own IP from step 2, not this example one)

If it still doesn't load, your computer's firewall may be blocking incoming connections on port 8000 — Windows will usually prompt to allow this the first time; allow it for at least "Private networks."
