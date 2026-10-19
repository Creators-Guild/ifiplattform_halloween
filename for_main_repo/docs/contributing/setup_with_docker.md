# Setup with Docker (recommended)

Last updated: 2026-10-20

The recommended way to run the project on your own computer. One step
installs everything: Python, the packages, a PostgreSQL database and some
test content. You don't need to know Docker to follow this. If
you're curious what it does, read the [Docker guide](docker_guide.md).

Can't use Docker? Use the [setup without Docker](setup_without_docker.md)
instead.

**Before you start:** [get the code](get_the_code.md). You need the
`IfiPlatform` folder on your computer.

## 1. Install the tools
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows and macOS). On Linux, install Docker Engine with the Compose plugin.
- [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension (by Microsoft).

Start Docker Desktop and leave it running. On Linux there's no Docker Desktop app, so start the Docker service instead:
```bash
sudo systemctl enable --now docker
```
This does two things. `--now` starts Docker right away, and `enable` makes it start by itself every time your computer boots. Docker then keeps running in the background, so you only run this once.

Rather start Docker yourself each time you need it? Use `sudo systemctl start docker` instead. It starts Docker now, but not after a restart.

## 2. Open the project in the container
1. Open the repo's root folder (`IfiPlatform`) in VS Code.
2. VS Code shows a popup: **"Reopen in Container"**. Click it. (No popup? Open the Command Palette with Ctrl+Shift+P, or Cmd+Shift+P on macOS, and run `Dev Containers: Reopen in Container`.)
3. Wait. The first time takes a few minutes, because Docker downloads Python and PostgreSQL and installs the packages. Later starts take seconds.

While it starts, the container sets up the database, fills it with test pages and starts the website. The [Docker guide](docker_guide.md#what-happens-when-you-click-reopen-in-container) shows each step.

## 3. Open the site
Go to http://localhost:8000.

The test content comes with a superuser: log in as `admin` with the password `admin`. It works both in Wagtail, where you edit pages (http://localhost:8000/wagtail-admin), and in the Django admin, with users and raw database tables (http://localhost:8000/admin). The login only exists in your local database.

## 4. You're in
- The VS Code terminal now runs **inside** the container, and you're already in the `ifiplatform/` folder, where `manage.py` is.
- You don't need a venv or a `.env` file. A `.env` is only for optional keys, like the DeepL key: see [Keys and tokens](docker_guide.md#keys-and-tokens-env).
- The site reloads when you save a file, so you don't need to run `runserver`. Just refresh the browser.

## Check that it works
- [ ] http://localhost:8000 shows the site.
- [ ] You can log in as `admin` / `admin` at http://localhost:8000/wagtail-admin.
- [ ] The quick tests pass in the VS Code terminal:
  ```bash
  python manage.py test --exclude-tag=slow
  ```

Something wrong? See [If something goes wrong](docker_guide.md#if-something-goes-wrong).

## Next
- New to Django? Read [How this project works](how_this_project_works.md). It explains the folders and where to find things.
- Make your first change: [Make a change, step by step](../../CONTRIBUTING.md#2-make-a-change-step-by-step).
- Using Docker day to day (restart or rebuild, your own extensions, fixing problems): [Docker guide](docker_guide.md).
