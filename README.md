# IfiPlatform
Student platform for IFI-UIO by students for students

## About
Goals:
- One place find information for IFI-students
- One place to find IFI-tools (ex. Peoply, Trix, IFI Rom etc.)
- A growing student library with study-resources made by IFI-students with main focus on IFI-subjects (based on IFI curriculum) and reuse
- A collection of study tools to build and represent study-resources (ex. flashcards, multiple choice, mock exam etc.)
- A low-threshold way for students — including those with little to no development experience — to contribute to and help shape the platform, building an open community around it

Note: the site is bilingual (Norwegian Bokmål + English) via wagtail-localize — new content pages generally need both locales.

## Tech stack
Django + Wagtail (Python, HTML and CSS, plus a little JavaScript), wagtail-localize for Norwegian/English, and PostgreSQL. Full list: [docs/architecture/tech_stack.md](docs/architecture/tech_stack.md).

## Quick start
The recommended setup is Docker. One step installs everything: Python, the packages, a PostgreSQL database and test data. Can't use Docker? See [setup without Docker](docs/contributing/setup_without_docker.md).

### 1. Install the tools
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows and macOS). On Linux, install Docker Engine with the Compose plugin.
- [Visual Studio Code](https://code.visualstudio.com/) with the **Dev Containers** extension (by Microsoft).

Start Docker Desktop and leave it running.

### 2. Open the project in the container
1. **Fork** the repo on GitHub (the "Fork" button at the top right), then clone your fork and connect it to the main repo:
   ```bash
   git clone https://github.com/<your-username>/IfiPlatform.git
   cd IfiPlatform
   git remote add upstream https://github.com/Creators-Guild/IfiPlatform.git
   ```
   `origin` is now your own fork, which is where you push. `upstream` is the main repo, where you get everyone else's changes. Collaborators with write access clone this repo directly instead, skip the last line, and use `origin` wherever the docs say `upstream`.

   **On Windows**, clone inside WSL, not to a drive like `C:\`: open the Ubuntu terminal, clone there, and run `code .` in the repo folder. Docker is much faster that way.

   Then open the repo's root folder in VS Code.
2. VS Code shows a popup: **"Reopen in Container"**. Click it. (No popup? Open the Command Palette and run `Dev Containers: Reopen in Container`.)
3. Wait. The first time takes a few minutes, because Docker downloads Python and PostgreSQL and installs the packages. Later starts take seconds.

While it starts, the container sets up the database, fills it with test data (`seed_dev_data`) and starts the website.

### 3. Open the site
Go to http://localhost:8000.

To edit pages, log in at http://localhost:8000/wagtail-admin with username `admin` and password `admin`. This is a test admin user that the test data (`seed_dev_data`) creates in your local database only. It doesn't exist on the real site, so you can't use it there, and it's never created when `DEBUG` is off.

### 4. Start working
The VS Code terminal now runs **inside** the container, and you're already in the `ifiplatform/` folder. You don't need a venv or a `.env` file. The site reloads when you save a file, so you don't need to run `runserver`.

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
| Edit pages and articles | http://localhost:8000/wagtail-admin (`admin` / `admin`) |
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
