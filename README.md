# Welcome to IfiPlattform Halloween 🎃

This is the repo for **Commit for Candy**, the event where IfiPlattform goes open source. For one evening we host a mock copy of [IfiPlattform](https://github.com/Creators-Guild/IfiPlatform) and get it ready for Halloween, together. Our goal: merge every contribution... and maybe, just maybe, not crash the site. ☠️

📅 **19 October 2026 at 18:00**
> 🎉Ifi Plattform blir Open Source🎉
>
> Det blir faglige presentasjoner og hurtigkurs i Open Source og hvordan å bidra i GitHub prosjekter etterfulgt pizza,🍕 bar og Commit for Candy (and Dr*nks!) med halloween som tema🎃👻🍬
>
> Arrangementet er et lavterskeltilbud for alle, uansett ferdighetsnivå, som vil bidra til et større studentprosjekt til nytte for hele IFI. Vi kommer til å hoste en mock-nettside av Ifi Plattform og gjøre den klar til halloween. Målet er å godkjenne alle bidrag... Kanskje vi til og med får til å ikke krasje den?☠️
>
> Ønsker du å gjøre noe mer enn å bare sitte på skolebenken og lære masse teori? Ønsker du å få hendene på noe og faktisk bygge noe?

## How the event works
- **Everyone is welcome**, whatever your skill level. You don't need to have used Git, Django or open source before.
- **Link your GitHub username.** Sign up on the mock site at https://halloween.ifiplattform.no, open **My issues** (https://halloween.ifiplattform.no/commits/) and add your GitHub username. You need it to claim issues and get points.
- **Claim an issue on the site.** The [Issues page](https://halloween.ifiplattform.no/commits/issues/) lists things to change and restyle for Halloween, from a single colour to whole pages. Press **Claim** on a free one, or **🎲 Give me an issue** to get a random one. Don't comment on GitHub to claim: only claims on the site count.
- **Collect points.** Each issue has a size: 🍬 candy = 1 point, 🍫 chocolate = 2, 🎃 pumpkin = 3. Start with a 🍬. You get the points when your issue is closed, and they show on the [Leaderboard](https://halloween.ifiplattform.no/commits/leaderboard/).
  - You can hold 2 issues at a time.
  - A claim runs out after 30 minutes (🍬), 60 (🍫) or 90 (🎃) unless you press **Keep**. Once you open a pull request, your claim no longer runs out.
- **Make the change** on your own computer (see [Get started](#get-started) below), then open a pull request.
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

## Get started
Two steps, and both end with the site running at http://localhost:8000.

**1. Get the code:** [Get the code](docs/contributing/get_the_code.md). At the event you're a **contributor**, so you fork the repo.

**2. Run the site.** Pick one:
- 🐳 **[Setup with Docker](docs/contributing/setup_with_docker.md) (recommended).** One click installs everything: Python, the packages, a database and the Halloween starter content.
- 🐍 **[Setup without Docker](docs/contributing/setup_without_docker.md).** Plain Python and SQLite, for laptops where Docker is too heavy or won't install.

## Next steps
1. **Set up** with the two steps above.
2. **Make your first change:** follow [Make a change, step by step](CONTRIBUTING.md#2-make-a-change-step-by-step) in CONTRIBUTING.md.

You don't have to read anything else first. The issues explain what to change and usually where, so you can start right away.

If you want more background, or you're on a harder issue, these short pages can help:
- [How this project works](docs/contributing/how_this_project_works.md): Django in plain words, the folders, and **where to change what**
- [Everyday commands](docs/contributing/everyday_commands.md): tests, migrations and translations
- [Tutorials](TUTORIALS.md): beginner guides to Git, Docker, Django, HTML and CSS

Stuck? Ask one of the helpers at the event. That's what they're there for.

## Everyday commands
With Docker, run these in the VS Code terminal (it's inside the container). Without Docker, run them in the `ifiplatform/` folder with your venv active.

| What | Command |
| --- | --- |
| Run the quick tests | `python manage.py test --exclude-tag=slow` |
| After changing a model | `python manage.py makemigrations` then `python manage.py migrate` |
| Edit pages and articles | http://localhost:8000/wagtail-admin (sign up first at http://localhost:8000/account/signin) |
| Users and raw database tables | http://localhost:8000/admin (needs `python manage.py createsuperuser`) |

More, including translations: [docs/contributing/everyday_commands.md](docs/contributing/everyday_commands.md). Docker day to day (stopping, resetting, fixing problems): [docs/contributing/docker.md](docs/contributing/docker.md).

## Docs
All docs, sorted by topic: [docs/README.md](docs/README.md).

- **Start here:** [How this project works](docs/contributing/how_this_project_works.md), the beginner's map: where things are and what the words mean
- **The full map, when you want more:** [overview.md](docs/architecture/overview.md), with diagrams of every app, the page tree and how a request becomes a page
- **Working on the code:**
  - [frontend.md](docs/architecture/frontend.md): how templates and CSS are organized and written
  - Features: [articles](docs/architecture/ifi_home_app/articles.md), [events](docs/architecture/ifi_home_app/events.md), [unions and tools](docs/architecture/ifi_home_app/unions_and_tools.md), [menus](docs/architecture/ifi_home_app/menus.md)
  - [management_commands.md](docs/operations/management_commands.md): this project's own `manage.py` commands
- **Design:** [Figma files](docs/design/figma_links.md) and the [feature concept map](docs/architecture/eraser_links.md)
- **Looking for something to fix?** At the event, start with a 🍬 candy issue on the [Issues page](https://halloween.ifiplattform.no/commits/issues/). Besides those, [to_fix.md](docs/to_fix.md) lists known bugs that don't have an issue yet.
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

## After the event
This repo will be **archived** some time after the event. It then becomes read-only, but nothing is deleted: the code, issues and pull requests stay here, so your contributions stay visible.

Good changes (bug fixes and improvements, not the Halloween look) may be moved into the real [IfiPlattform](https://github.com/Creators-Guild/IfiPlatform) repo, with you still credited as the author. Want to keep contributing? Head over there.
