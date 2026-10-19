# Everyday commands

Last updated: 2026-10-20

These work the same in both setups. With Docker, run them in the container's terminal.

For a full list and explanation of this project's custom `manage.py` commands (beyond the built-in Django ones below), see [operations/management_commands.md](../operations/management_commands.md).

## If you change a model (i.e. need a new migration)
```bash
python manage.py makemigrations
python manage.py migrate
```
## To create superuser/admin user
`seed_dev_data` (runs on every Docker start, or step 7 of the [setup without Docker](setup_without_docker.md)) already creates an `admin` / `admin` superuser for
local development, so you usually don't need this. To make your own:
```bash
python manage.py createsuperuser
```
Fill out the terminal's questions
## Running tests
The quick tests, the ones to run before you open a pull request:
```bash
python manage.py test --exclude-tag=slow
```
This skips the slow whole-site crawler test (`core_app.tests.SiteCrawlTests`, tagged `slow`: it seeds a full page tree and makes real HTTP requests to every page on the site).

All tests, including the slow one:
```bash
python manage.py test
```
To test just one app, name it, e.g. `python manage.py test ifi_home_app`.

CI runs every test, the slow one too, on every PR (`.github/workflows/ci.yml`) across Python 3.12–3.14, so run `python manage.py test` yourself before you open a PR if you changed something big. CI uses PostgreSQL, like production and the Docker setup. Without Docker your tests run on SQLite instead, so now and then a test can pass for you and fail in CI.
## Translations
If you change translatable text (`{% trans %}` / `_(...)`):
Update the `.po` files with the new/changed strings:
```bash
python manage.py makemessages -l nb -l en
```
Then compile them so Django actually picks up the changes:
```bash
python manage.py compilemessages
```
If that fails because `msgfmt` (part of GNU gettext) isn't installed — common on Windows, and it needs admin rights to install via `choco install gettext` — use this project's pure-Python fallback instead:
```bash
python manage.py compile_translations
```
See [operations/management_commands.md](../operations/management_commands.md#compile_translations) for why this exists.
## Log in on admin interface or wagtail-admin interface
Log in via a superuser you have created.
```
http://localhost:8000/admin
```
Django's own admin — user accounts, permissions, raw model tables.
```
http://localhost:8000/wagtail-admin
```
Wagtail's CMS admin — this is where you edit articles, categories and their index pages.
- Highly recommend filling the database with seed data first (see above) so you can see the real page structure.
