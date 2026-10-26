# IfiPlatform
Student platform for IFI-UIO by students for students

## About
Goals:
- One place find information for IFI-students
- One place to find IFI-tools (ex. Peoply, Trix, IFI Rom etc.)
- A growing student library with study-resources made by IFI-students with main focus on IFI-subjects (based on IFI curriculum) and reuse
- A collection of study tools to build and represent study-resources (ex. flashcards, multiple choice, mock exam etc.)
- A low-threshold way for students — including those with little to no development experience — to contribute to and help shape the platform, building an open community around it

Note: the site is bilingual (Norwegian Bokmål + English). Pages are written in Norwegian; DeepL fills in the English, and editors can correct it. See [docs/architecture/shared/translations.md](docs/architecture/shared/translations.md).

## Tech stack
Django + Wagtail (Python, HTML and CSS, plus a little JavaScript), DeepL for Norwegian → English, and PostgreSQL. Full list: [docs/architecture/tech_stack.md](docs/architecture/tech_stack.md).

## Get started
Two steps, and both end with the site running at http://localhost:8000.

**Recommended to set up with Docker Desktop and Visual Studio Code.** Download Docker, VSC and add the extension **Dev Containers**. More info in the setup with docker below.

**1. Get the code:** [Get the code](docs/contributing/get_the_code.md). Most people are **contributors** and fork the repo. Collaborators with write access clone it directly.

**2. Run the site.** Pick one:
- 🐳 **[Setup with Docker](docs/contributing/setup_with_docker.md) (recommended).** One click installs everything: Python, the packages, a database and test content.
- 🐍 **[Setup without Docker](docs/contributing/setup_without_docker.md).** Plain Python and SQLite, for laptops where Docker is too heavy or won't install.

## Next steps
1. **Set up** with the two steps above.
2. **Make your first change.** With Docker, run these in the VS Code terminal:
   ```bash
   ifi fix-issue 42        # a branch for issue #42, made from the newest code
   # ...make your change, check it at http://localhost:8000...
   ifi test                # the quick tests
   ifi save "Short description of what you changed"   # git add + commit, for the whole repo
   ifi pull-request        # pushes, and gives you the pull request link
   ifi update              # later: bring your branch up to date with the newest main
   ```
   `ifi` commands are this project's own shortcuts, not part of Git. Each one prints the commands it runs. Rather do it all with Git, or not using Docker? Follow [Make a change, step by step](CONTRIBUTING.md#2-make-a-change-step-by-step) in CONTRIBUTING.md.

If you want more background first, these short pages can help:
- [How this project works](docs/contributing/how_this_project_works.md): Django in plain words, the folders, and **where to change what**
- [Everyday commands](docs/contributing/everyday_commands.md): tests, migrations and translations
- [Tutorials](TUTORIALS.md): beginner guides to Git, Docker, Django, HTML and CSS

## Everyday commands
With Docker, run these in the VS Code terminal (it's inside the container). Without Docker, run them in the `ifiplatform/` folder with your venv active.

| What | Command |
| --- | --- |
| Run the quick tests | `python manage.py test --exclude-tag=slow`, or `ifi test` |
| After changing a model | `python manage.py makemigrations` then `python manage.py migrate`, or `ifi migrate` |
| Edit pages and articles | http://localhost:8000/wagtail-admin (`admin` / `admin`) |
| Users and raw database tables | http://localhost:8000/admin |

Forgot a command? Type `ifi help`. Without Docker, run `./ifi install` once first (see [setup without Docker](docs/contributing/setup_without_docker.md#optional-the-ifi-commands)). Something not working? `ifi check` checks your setup and says what to fix. Every `ifi` command lists what it did for you under "Done for you:", a ✓ line for each step with the Git command under it. Then "In plain Git, this was:", so you can type them yourself next time, and "Your turn:" with what you can do next.

More, including translations: [docs/contributing/everyday_commands.md](docs/contributing/everyday_commands.md). Docker day to day (restart or rebuild, fixing problems): [docs/contributing/docker_guide.md](docs/contributing/docker_guide.md).

## Docs
All docs, sorted by topic: [docs/README.md](docs/README.md).

- **Start here:** [How this project works](docs/contributing/how_this_project_works.md), the beginner's map: where things are and what the words mean
- **The full map, when you want more:** [overview.md](docs/architecture/overview.md), with diagrams of every app, the page tree and how a request becomes a page
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
