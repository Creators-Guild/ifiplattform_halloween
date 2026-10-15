# Setup with Docker (recommended)

Last updated: 2026-10-15

The recommended way to run the project on your own computer. One step
installs everything: Python, the packages, a PostgreSQL database and the
Halloween test content. You don't need to know Docker to follow this. If
you're curious what it does, read the [Docker guide](docker_guide.md).

Can't use Docker? Use the [setup without Docker](setup_without_docker.md)
instead.

**Before you start:** [get the code](get_the_code.md). You need the
`ifiplattform_halloween` folder on your computer.

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
1. Open the repo's root folder (`ifiplattform_halloween`) in VS Code.
2. VS Code shows a popup: **"Reopen in Container"**. Click it. (No popup? Open the Command Palette with Ctrl+Shift+P, or Cmd+Shift+P on macOS, and run `Dev Containers: Reopen in Container`.)
3. Wait. The first time takes a few minutes, because Docker downloads Python and PostgreSQL and installs the packages. Later starts take seconds.

While it starts, the container sets up the database, fills it with the Halloween starter content and starts the website. The [Docker guide](docker_guide.md#what-happens-when-you-click-reopen-in-container) shows each step.

## 3. Open the site
Go to http://localhost:8000.

To edit pages, sign up at http://localhost:8000/account/signin with any username and password. You can edit pages at once, at http://localhost:8000/wagtail-admin. The login only exists in your local database.

For the Django admin (users and raw database tables, at http://localhost:8000/admin) you need a superuser. Run this in the VS Code terminal and answer the questions:
```bash
python manage.py createsuperuser
```

## 4. You're in
- The VS Code terminal now runs **inside** the container, and you're already in the `ifiplatform/` folder, where `manage.py` is.
- You don't need a venv or a `.env` file. A `.env` is only for optional keys, like the GitHub token: see [Keys and tokens](docker_guide.md#keys-and-tokens-env).
- The site reloads when you save a file, so you don't need to run `runserver`. Just refresh the browser.

## Check that it works
- [ ] http://localhost:8000 shows the Halloween site.
- [ ] You can sign up and open http://localhost:8000/wagtail-admin.
- [ ] The quick tests pass in the VS Code terminal:
  ```bash
  python manage.py test --exclude-tag=slow
  ```

Something wrong? See [If something goes wrong](docker_guide.md#if-something-goes-wrong), or ask a helper.

## Next
- New to Django? Read [How this project works](how_this_project_works.md). It explains the folders and where to find things.
- Make your first change: [Make a change, step by step](../../CONTRIBUTING.md#2-make-a-change-step-by-step).
- Using Docker day to day (restart or rebuild, your own extensions, fixing problems): [Docker guide](docker_guide.md).
