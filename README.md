# Welcome to IfiPlattform Halloween 🎃

This is the repo for **Commit for Candy**, the event where IfiPlattform goes open source. For one evening we host a mock copy of [IfiPlattform](https://github.com/Creators-Guild/IfiPlatform) and get it ready for Halloween, together. The aim is to approve every contribution... and maybe even not crash it? ☠️

📅 **19 October 2026 at 18:00**. More details (place, programme) are coming.

> 🎉Ifi Plattform blir Open Source🎉
>
> Det blir faglige presentasjoner og hurtigkurs i Open Source og hvordan å bidra i GitHub prosjekter etterfulgt pizza,🍕 bar og Commit for Candy (and Dr*nks!) med halloween som tema🎃👻🍬
>
> Arrangementet er et lavterskeltilbud for alle, uansett ferdighetsnivå, som vil bidra til et større studentprosjekt til nytte for hele IFI. Vi kommer til å hoste en mock-nettside av Ifi Plattform og gjøre den klar til halloween. Målet er å godkjenne alle bidrag... Kanskje vi til og med får til å ikke krasje den?☠️
>
> Ønsker du å gjøre noe mer enn å bare sitte på skolebenken og lære masse teori? Ønsker du å få hendene på noe og faktisk bygge noe?

## How the event works
- **Everyone is welcome**, whatever your skill level. You don't need to have used Git, Django or open source before.
- **Pick an issue.** The [Issues tab](https://github.com/Creators-Guild/ifiplattform_halloween/issues) is filled with things to change and restyle for Halloween, from a single colour to whole pages. Comment on one to claim it.
- **Make the change** on your own computer (see [Quick start](#quick-start) below), then open a pull request.
- **See it live.** When your pull request is merged, the mock site at https://halloween.ifiplattform.no updates by itself within a few minutes.
- **Edit content on the mock site.** Sign up there with just a username and password, and you can write and publish pages right away. Don't use your real name or a password you use anywhere else: this is a test site.

## About IfiPlattform
IfiPlattform is a student platform for IFI-UIO, by students for students.

Goals:
- One place find information for IFI-students
- One place to find IFI-tools (ex. Peoply, Trix, IFI Rom etc.)
- A growing student library with study-resources made by IFI-students with main focus on IFI-subjects (based on IFI curriculum) and reuse
- A collection of study tools to build and represent study-resources (ex. flashcards, multiple choice, mock exam etc.)
- A low-threshold way for students — including those with little to no development experience — to contribute to and help shape the platform, building an open community around it

Note: the site is bilingual (Norwegian Bokmål + English). Pages are written in Norwegian; DeepL fills in the English, and editors can correct it. See [docs/architecture/shared/translations.md](docs/architecture/shared/translations.md).

## Tech stack
Django + Wagtail (Python, HTML and CSS, plus a little JavaScript), DeepL for Norwegian → English, and PostgreSQL. Full list: [docs/architecture/tech_stack.md](docs/architecture/tech_stack.md).

## Quick start
The recommended setup is Docker. One step installs everything: Python, the packages, a PostgreSQL database and test data. Can't use Docker? See [setup without Docker](docs/contributing/setup_without_docker.md).

### 1. Install the tools
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows and macOS). On Linux, install Docker Engine with the Compose plugin.
- [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension (by Microsoft).
- **Recommended if you're not comfortable with Git:** [GitHub Desktop](https://desktop.github.com/). It lets you clone, commit, push and open pull requests with buttons instead of commands. If you already use Git in the terminal, you don't need it.

Start Docker Desktop and leave it running. On Linux there's no Docker Desktop app — start the daemon instead:
```bash
sudo systemctl start docker
sudo systemctl enable --now docker
```

### 2. Open the project in the container
1. **Fork** the repo on GitHub (the "Fork" button at the top right), then clone your fork and connect it to the main repo:
   ```bash
   git clone https://github.com/<your-username>/ifiplattform_halloween.git
   cd ifiplattform_halloween
   git remote add upstream https://github.com/Creators-Guild/ifiplattform_halloween.git
   ```
   `origin` is now your own fork, which is where you push. `upstream` is the main repo, where you get everyone else's changes. Collaborators with write access clone this repo directly instead, skip the last line, and use `origin` wherever the docs say `upstream`.

   **With GitHub Desktop:** fork the repo on GitHub as above, then in GitHub Desktop choose **File → Clone repository** and pick your fork. When it asks how you plan to use the fork, choose **"To contribute to the parent project"**. That sets up the connection to the main repo for you.

   **On Windows**, clone inside WSL, not to a drive like `C:\`: open the Ubuntu terminal, clone there, and run `code .` in the repo folder. Docker is much faster that way. GitHub Desktop always clones to a Windows folder, so the site runs slower with it, but it still works.

   Then open the repo's root folder in VS Code.
2. VS Code shows a popup: **"Reopen in Container"**. Click it. (No popup? Open the Command Palette and run `Dev Containers: Reopen in Container`.)
3. Wait. The first time takes a few minutes, because Docker downloads Python and PostgreSQL and installs the packages. Later starts take seconds.

While it starts, the container sets up the database, fills it with the Halloween starter content (`seed_halloween_data`) and starts the website.

### 3. Open the site
Go to http://localhost:8000.

To edit pages, sign up at http://localhost:8000/account/signin with any username and password. You can edit pages at once, at http://localhost:8000/wagtail-admin. The login only exists in your local database. For the Django admin (users and raw database tables) you need a superuser: run `python manage.py createsuperuser` in the VS Code terminal.

### 4. Start working
The VS Code terminal now runs **inside** the container, and you're already in the `ifiplatform/` folder. You don't need a venv or a `.env` file (only for optional keys, like the GitHub token: see [docs/contributing/docker.md](docs/contributing/docker.md#keys-and-tokens-env)). The site reloads when you save a file, so you don't need to run `runserver`.

## Next steps
- **Make your first change:** follow [Your First Contribution, Step by Step](CONTRIBUTING.md#your-first-contribution-step-by-step) in CONTRIBUTING.md.
- **Using Docker day to day** (your own extensions, stopping and resetting, when something goes wrong): [docs/contributing/docker.md](docs/contributing/docker.md)
- **Commands you'll use often:** [docs/contributing/everyday_commands.md](docs/contributing/everyday_commands.md)

## Everyday commands
Run these in the container's terminal.

| What | Command |
| --- | --- |
| Run the quick tests | `python manage.py test --exclude-tag=slow` |
| After changing a model | `python manage.py makemigrations` then `python manage.py migrate` |
| Edit pages and articles | http://localhost:8000/wagtail-admin (sign up first, see [Open the site](#3-open-the-site)) |
| Users and raw database tables | http://localhost:8000/admin |

More, including translations: [docs/contributing/everyday_commands.md](docs/contributing/everyday_commands.md).

## Docs
All docs, sorted by topic: [docs/README.md](docs/README.md).

- **Start here:** [overview.md](docs/architecture/overview.md), the map of the whole system: apps, the page tree and how a request becomes a page
- **Working on the code:**
  - [frontend.md](docs/architecture/frontend.md): how templates and CSS are organized and written
  - Features: [articles](docs/architecture/ifi_home_app/articles.md), [events](docs/architecture/ifi_home_app/events.md), [unions and tools](docs/architecture/ifi_home_app/unions_and_tools.md), [menus](docs/architecture/ifi_home_app/menus.md)
  - [management_commands.md](docs/operations/management_commands.md): this project's own `manage.py` commands
- **Design:** [Figma files](docs/design/figma_links.md) and the [feature concept map](docs/architecture/eraser_links.md)
- **Looking for something to fix?** Besides issues labeled `good first issue`, [to_fix.md](docs/to_fix.md) lists known bugs that don't have an issue yet.
- **Production (maintainers):** [prod_server.md](docs/operations/prod_server.md)
- **Picking up an AI-drafted doc to finish by hand?** See [docs/claude_references/readme.md](docs/claude_references/readme.md). Those are starting points, not final docs.

## Tutorials
Check out [TUTORIALS.md](TUTORIALS.md) for more about Django Framework and other dependencies used in this project.

## Contributing
We welcome contributions mainly from IFI students(with certain exceptions)! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to open issues (bug/feature/task reports, with examples)
- How to submit pull requests
- Code style expectations (Black/Pylint)
- The different contributor roles in this project
- Precisely who can contribute

## License
This project is licensed under the [MIT License](LICENSE).
