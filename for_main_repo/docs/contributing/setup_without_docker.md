# Setup without Docker (Python + SQLite)

Last updated: 2026-10-26

Only use this if Docker is too heavy for your laptop or won't install. The
recommended setup is [Setup with Docker](setup_with_docker.md).

Here you install Python packages yourself and use SQLite, a database that
is just one file on your computer. The site looks the same as in Docker.

**Before you start:** [get the code](get_the_code.md). You need the
`IfiPlatform` folder on your computer.

## Requirements
- Python 3.12 or newer (tested on 3.12, 3.13 and 3.14)
- [Visual Studio Code](https://code.visualstudio.com/) (recommended)
- SQLite, which comes with Python

**About folders:** cloning gives you a folder called `IfiPlatform`
(the "repo root"). Inside it is a folder called `ifiplatform`, where
`manage.py` and the Django code live. Each step says which folder to run it in.

## 1. Open the project in VS Code
Open the `IfiPlatform` folder in VS Code. If VS Code offers to
"Reopen in Container", say no: that's the Docker setup.

## 2. Make a virtual environment
A virtual environment (venv) is a private box for this project's Python
packages, so they don't mix with anything else on your computer. Run this in
the repo root:

**Windows (PowerShell)**
```bash
py -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell says running scripts is disabled, run this once and try again:
```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Or in VS Code:** Command Palette (Ctrl+Shift+P) → `Python: Create Environment`.

When it's active, your terminal prompt starts with `(venv)`. Activate it
again every time you open a new terminal.

## 3. Install the packages
In the repo root:
```bash
pip install -r requirements.txt
```
In VS Code, click **Install** when it offers the project's recommended
extensions (Python, Black, Pylint, Django templates and Mermaid diagrams). Then pick your venv
with Command Palette → `Python: Select Interpreter`, so the editor uses the
same Black and pylint versions as everyone else. Black formats Python files
when you save, just like in Docker.

## 4. Move into the ifiplatform folder
```bash
cd ifiplatform
```
Every command from here on is run in this folder.

## 5. Create the .env file
The `.env` file holds settings for your own computer. Copy the example:
```bash
cp .env.example .env
```
(In PowerShell `cp` works too. In the old Windows `cmd`, use `copy`.)

If you skip this step, Django stops with `DJANGO_SECRET_KEY is not set`.

**The secret key.** Django uses `DJANGO_SECRET_KEY` to sign logins and
other data, so on a real server it must be a long random value that
nobody else knows. On your own computer the placeholder from the example
works fine. To use a proper key anyway, generate one:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Copy what it prints into `.env`, after `DJANGO_SECRET_KEY=` (no spaces or
quotes). Run the command with your venv active, since it needs Django. If
you change the key later, you're logged out of your local site, but nothing
else breaks.

The rest of the example values work as they are.

## 6. Create the database
```bash
python manage.py migrate
```
This creates `db.sqlite3` and all the tables in it.

## 7. Fill it with test content
```bash
python manage.py seed_dev_data
```
This adds the same test pages as the Docker setup: categories, articles,
news, events, student unions, tools and menus, plus an `admin` login. It
skips what already exists, so it's safe to run again. See
[management_commands.md](../operations/management_commands.md#seed_dev_data).

## 8. Start the site
```bash
python manage.py runserver
```
Open http://localhost:8000. The server reloads when you save a file. Stop it
with Ctrl+C.

## 9. Log in
The test content comes with a superuser: log in as `admin` with the
password `admin`. It works both in Wagtail, where you edit pages
(http://localhost:8000/wagtail-admin), and in the Django admin
(http://localhost:8000/admin). The login only exists in your local
database.

## Check that it works
- [ ] http://localhost:8000 shows the site.
- [ ] You can log in as `admin` / `admin` at http://localhost:8000/wagtail-admin.
- [ ] The quick tests pass:
  ```bash
  python manage.py test --exclude-tag=slow
  ```

Your tests run on SQLite, while CI uses PostgreSQL. Now and then a test can
pass for you and fail in CI. That's not your fault: say so in your pull request.

## Optional: the `ifi` commands
The project's own shortcuts (`ifi check`, `ifi save`, `ifi pull-request`,
`ifi test`, ...) work without Docker too. They're bash scripts, so on
Windows use the **Git Bash** terminal (it comes with Git for Windows; in VS
Code pick it with the **+** arrow in the terminal panel). In the repo root:
```bash
./ifi install
```
Open a new terminal, and `ifi help` lists them. They find your venv by
themselves. In PowerShell, run them from the repo root as `.\ifi check`
instead (that still needs Git Bash installed).

## Next
- New to Django? Read [How this project works](how_this_project_works.md).
- Make your first change: [Make a change, step by step](../../CONTRIBUTING.md#2-make-a-change-step-by-step).
- Commands you'll use often: [everyday_commands.md](everyday_commands.md).

## Extra: open the site on your phone (same Wi-Fi)
Useful for testing the mobile layout on a real device. This only works with
this setup: the Docker setup only accepts connections from your own computer.

1. Start the server so it listens on your network, not just your computer:
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
   Without this, Django rejects the request with a 400 `DisallowedHost` error.
4. On your phone, connected to the **same Wi-Fi network**, open
   `http://192.168.1.23:8000` (with your own IP from step 2).

If it still doesn't load, your computer's firewall may be blocking port
8000. Windows usually asks the first time: allow it for at least "Private
networks".
