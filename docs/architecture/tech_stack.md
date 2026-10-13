# Tech stack

Last updated: 2026-10-11

What IfiPlatform is built with, and why each piece is there. For how the
production server runs all of this, see
[operations/prod_server.md](../operations/prod_server.md). For getting a
local copy running, see the main [README.md](../../README.md).

## At a glance

| Layer              | Technology                                           |
| ------------------ | ---------------------------------------------------- |
| Language           | Python (CI tests 3.12, 3.13 and 3.14)                |
| Web framework      | Django 6.0                                           |
| CMS / admin        | Wagtail 7.4                                          |
| Translation        | wagtail-localize + DeepL machine translation         |
| Database           | PostgreSQL (production), SQLite (local default)      |
| Frontend           | Django templates, plain CSS (ITCSS + BEM)            |
| Web server         | Nginx (reverse proxy, HTTPS) + Gunicorn (WSGI)       |
| Hosting            | NREC (Norwegian Research and Education Cloud)        |
| Code hosting & CI  | GitHub + GitHub Actions                              |

The exact version of every Python package is pinned in
[requirements.txt](../../requirements.txt).

## Backend

- **Django 6.0**: the web framework everything else is built on.
- **Wagtail 7.4**: the CMS. Articles, categories, events, student unions
  and their index pages are Wagtail pages, edited in the Wagtail admin
  at `/<lang>/wagtail-admin/`. Wagtail brings its own helpers with it: `django-modelcluster`,
  `django-treebeard` (the page tree), `django-taggit` (tags) and `Willow`
  (image handling).
- **wagtail-localize**: keeps a Norwegian Bokmål (`nb`, the default) and an
  English (`en`) version of each page in sync.
- **Django REST framework**: in `requirements.txt`, but not wired up yet
  (not in `INSTALLED_APPS`, no API endpoints).
- **psycopg 3**: the PostgreSQL driver.
- **python-dotenv**: loads settings and secrets from the `.env` file (see
  [Configuration](#configuration)).

## Django apps

The Django project lives in `ifiplatform/`. Settings and root URLs are in
`ifiplatform_project/`.

| App             | Location                     | Responsibility                                                  |
| --------------- | ---------------------------- | --------------------------------------------------------------- |
| `core_app`      | `ifiplatform/core_app/`      | Shared infrastructure: deploy notice banner, sitemap, static file storage, "under development" placeholders |
| `ifi_home_app`  | `ifiplatform/apps/`          | Homepage, articles, categories, events, student unions, translation tooling |
| `account_app`   | `ifiplatform/apps/`          | Sign-up, login, email verification, editor terms                |
| `study_app`     | `ifiplatform/apps/`          | Study resources (under development)                             |
| `yourpage_app`  | `ifiplatform/apps/`          | Personal user page (under development)                          |

Sections still under development show a placeholder page instead of their
real views. This is controlled by `APPS_UNDER_DEVELOPMENT` in `settings.py`.

## Database

- **Production:** PostgreSQL, running on the same server as the app.
- **Local development, Python setup:** SQLite (`db.sqlite3`, no setup
  needed).
- **Local development, Docker setup:**
  [docker-compose.yml](../../docker-compose.yml) runs PostgreSQL 16 (`db`)
  and Django (`web`). Details in [docker_setup.md](docker_setup.md).

Which database is used depends on `DEBUG` and `USE_POSTGRES`. With `DEBUG`
off, it is always PostgreSQL.

## Frontend

Server-rendered Django templates with plain CSS: no JavaScript framework
and no CSS build step. The CSS follows ITCSS layers and BEM naming, and each
page only loads the CSS files it needs. The full rules are in
[frontend.md](frontend.md).

Static files get a content hash in their names in production (for example
`article_page.a1b2c3.css`), so browsers pick up new versions after a
deploy.

## Caching

A **file-based cache** (`ifiplatform/django_cache/`) is shared by all
Gunicorn worker processes, so a change seen by one worker is seen by all.
Tests use a separate in-memory cache.

## External services

| Service        | Used for                                                                 | Configured by                           |
| -------------- | ------------------------------------------------------------------------ | --------------------------------------- |
| **DeepL**      | Machine translation NB → EN, with a custom glossary of fixed terms        | `DEEPL_API_KEY`, `DEEPL_GLOSSARY_ID`    |
| **Peoply**     | Source of truth for events; synced into Wagtail event pages on a timer    | `sync_peoply_events` command            |
| **Umami**      | Privacy-friendly page analytics                                          | `UMAMI_SCRIPT_URL`, `UMAMI_WEBSITE_ID`  |
| **SMTP email** | Account verification emails (prints to the console when not configured)  | `EMAIL_HOST` and related keys           |

The management commands behind these integrations are documented in
[operations/management_commands.md](../operations/management_commands.md).

## Configuration

All environment-specific settings and secrets come from a `.env` file in
`ifiplatform/`. It is gitignored and never committed. The keys used in
production are listed in
[operations/prod_server.md](../operations/prod_server.md#environment-variables).

## Tooling and GitHub workflows

- **GitHub** hosts the code, issues and pull requests.
- **black** is used for code formatting. CI fails if a file isn't formatted.
- **pylint** (with pylint-django) checks code quality. Both are in
  `requirements.txt`, and the dev container's editor runs them.
- **GitHub Actions** workflows in `.github/workflows/`:

| Workflow                 | When it runs                                | What it does                                                     |
| ------------------------ | ------------------------------------------- | ---------------------------------------------------------------- |
| `ci.yml`                 | Every PR to `main`, by hand, before deploys | Runs the test suite on Python 3.12–3.14 against PostgreSQL 16, checks Black formatting, and runs pylint (fails below 7/10) |
| `automerge.yml`          | After CI passes on a PR                     | Merges the PR automatically if it has the `automerge` label      |
| `deploy.yml`             | Nightly at 01:00 UTC, or by hand            | Deploys `main` to production (see [prod_server.md](../operations/prod_server.md#deploy-flow)) |
| `trello_sync.yml`        | Issue opened, edited or closed              | Mirrors GitHub issues as Trello cards                            |
| `clean-issue-body.yml`   | Issue opened                                | Removes empty optional fields left by issue forms                |

## Hosting

Production runs on a single virtual machine in NREC, with Nginx in front of
Gunicorn and PostgreSQL on the same machine. Everything about that server
is in [operations/prod_server.md](../operations/prod_server.md).
