# Setup with Docker (recommended)

Last updated: 2026-10-15

The recommended way to run the project on your own computer. One step
installs everything: Python, the packages, a PostgreSQL database and the
Halloween test content. You don't need to know Docker to follow this. If
you're curious what it does, read [Docker, explained simply](docker_explained.md).

Can't use Docker? Use the [setup without Docker](setup_without_docker.md)
instead.

## 1. Install the tools
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows and macOS). On Linux, install Docker Engine with the Compose plugin.
- [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension (by Microsoft).
- **Recommended if you're not comfortable with Git:** [GitHub Desktop](https://desktop.github.com/). It lets you clone, commit, push and open pull requests with buttons instead of commands. If you already use Git in the terminal, you don't need it.

Start Docker Desktop and leave it running. On Linux there's no Docker Desktop app, so start the Docker service instead:
```bash
sudo systemctl enable --now docker
```
This does two things. `--now` starts Docker right away, and `enable` makes it start by itself every time your computer boots. Docker then keeps running in the background, so you only run this once.

Rather start Docker yourself each time you need it? Use `sudo systemctl start docker` instead. It starts Docker now, but not after a restart.

## 2. Fork and clone
**Fork** the repo on GitHub (the "Fork" button at the top right), then clone your fork and connect it to the main repo:
```bash
git clone https://github.com/<your-username>/ifiplattform_halloween.git
cd ifiplattform_halloween
git remote add upstream https://github.com/Creators-Guild/ifiplattform_halloween.git
```
`origin` is now your own fork, which is where you push. `upstream` is the main repo, where you get everyone else's changes:

![Fork and clone: upstream is our repo, origin is your fork, and your clone is on your computer](images/fork_and_clone.svg)

You only fork and clone once. After that the work goes in a loop: get the latest code from `upstream`, push your branch to `origin`, and open a pull request back to `upstream`.

**With GitHub Desktop:** fork the repo on GitHub as above, then in GitHub Desktop choose **File → Clone repository** and pick your fork. When it asks how you plan to use the fork, choose **"To contribute to the parent project"**. That sets up the connection to the main repo for you.

**On Windows**, clone inside WSL, not to a drive like `C:\`: open the Ubuntu terminal, clone there, and run `code .` in the repo folder. Docker is much faster that way. GitHub Desktop always clones to a Windows folder, so the site runs slower with it, but it still works.

## 3. Open the project in the container
1. Open the repo's root folder (`ifiplattform_halloween`) in VS Code.
2. VS Code shows a popup: **"Reopen in Container"**. Click it. (No popup? Open the Command Palette with Ctrl+Shift+P, or Cmd+Shift+P on macOS, and run `Dev Containers: Reopen in Container`.)
3. Wait. The first time takes a few minutes, because Docker downloads Python and PostgreSQL and installs the packages. Later starts take seconds.

While it starts, the container sets up the database, fills it with the Halloween starter content and starts the website. [Docker, explained simply](docker_explained.md#what-happens-when-you-click-reopen-in-container) shows each step.

## 4. Open the site
Go to http://localhost:8000.

To edit pages, sign up at http://localhost:8000/account/signin with any username and password. You can edit pages at once, at http://localhost:8000/wagtail-admin. The login only exists in your local database.

For the Django admin (users and raw database tables, at http://localhost:8000/admin) you need a superuser. Run this in the VS Code terminal and answer the questions:
```bash
python manage.py createsuperuser
```

## 5. You're in
- The VS Code terminal now runs **inside** the container, and you're already in the `ifiplatform/` folder, where `manage.py` is.
- You don't need a venv or a `.env` file. A `.env` is only for optional keys, like the GitHub token: see [Keys and tokens](docker.md#keys-and-tokens-env).
- The site reloads when you save a file, so you don't need to run `runserver`. Just refresh the browser.

## Check that it works
- [ ] http://localhost:8000 shows the Halloween site.
- [ ] You can sign up and open http://localhost:8000/wagtail-admin.
- [ ] The quick tests pass in the VS Code terminal:
  ```bash
  python manage.py test --exclude-tag=slow
  ```

Something wrong? See [If something goes wrong](docker.md#if-something-goes-wrong), or ask a helper.

## Next
- New to Django? Read [How this project works](how_this_project_works.md). It explains the folders and where to find things.
- Make your first change: [Make a change, step by step](../../CONTRIBUTING.md#2-make-a-change-step-by-step).
- Using Docker day to day (stopping, resetting, your own extensions): [docker.md](docker.md).
