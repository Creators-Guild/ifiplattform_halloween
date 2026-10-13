# docs/

Last updated: 2026-10-11

Project documentation beyond the main [README.md](../README.md). Each
folder holds one kind of document. When you add a new doc, put it in the
folder whose description fits, follow the [rules](#rules) below, and add a
line for it to the list.

Known problems waiting to become GitHub issues are listed in
[to_fix.md](to_fix.md).

## architecture/ — how the system is built

Start with the overview. Guides to how the project uses a framework (such
as `frontend.md`) sit directly in `architecture/`. Feature docs are sorted
into one folder per app, and features that span several apps go in
`shared/`.

- [overview.md](architecture/overview.md): the map of the whole system:
  apps, the Wagtail page tree, and the path from request to page
- [tech_stack.md](architecture/tech_stack.md): languages, frameworks,
  database, external services and GitHub workflows
- [frontend.md](architecture/frontend.md): how HTML templates and CSS are
  organized, loaded and written
- [docker_setup.md](architecture/docker_setup.md): how the local Docker
  setup is built and why
- [eraser_links.md](architecture/eraser_links.md): feature concept map
- `shared/`: cross-app features and `core_app` (no docs yet)
- `ifi_home_app/`: feature docs for the main site
  - [articles.md](architecture/ifi_home_app/articles.md): article,
    category and index pages, StreamField blocks, and article and block
    styles
  - [unions_and_tools.md](architecture/ifi_home_app/unions_and_tools.md):
    student union and tool pages
  - [events.md](architecture/ifi_home_app/events.md): event pages, the
    calendar and the Peoply sync
  - [menus.md](architecture/ifi_home_app/menus.md): how menus are
    modelled and rendered
- `account_app/`, `study_app/`: feature docs per app (no docs yet, see
  [Planned docs](#planned-docs))

## operations/ — how it runs in production

- [prod_server.md](operations/prod_server.md): the NREC server, deploy
  flow, security and routine checks
- [server_toolbox.md](operations/server_toolbox.md): how to use journalctl,
  systemctl, Nginx logs and friends to track down problems on the server
- [management_commands.md](operations/management_commands.md): this
  project's custom `manage.py` commands
- [backups_and_recovery.md](operations/backups_and_recovery.md): what is
  backed up, how to check it, and how to restore
- [server_setup.md](operations/server_setup.md): how to rebuild the
  production server from zero
- [access_and_handover.md](operations/access_and_handover.md): accounts
  and keys, and checklists for adding, removing and handing over people

## contributing/ — how to contribute

Guides for contributors beyond the basics in
[CONTRIBUTING.md](../CONTRIBUTING.md). More are planned (reviewing,
writing content, writing docs, testing), see [Planned docs](#planned-docs)
below.

- [docker.md](contributing/docker.md): using the Docker setup day to day:
  your own extensions, stopping and resetting, and fixing problems
- [setup_without_docker.md](contributing/setup_without_docker.md): the
  Python + SQLite setup, for when Docker won't work
- [everyday_commands.md](contributing/everyday_commands.md): migrations,
  tests, translations and the admin pages

## design/ — UI and visual design

- [figma_links.md](design/figma_links.md): Figma files

## claude_context/ and claude_references/ — for AI agents

`claude_context/` holds notes written for AI agents working on the code.
`claude_references/` holds AI-drafted starting points for docs that still
need to be finished by hand. Neither folder is documentation for people,
so the docs here don't link to them.

## Rules

1. **Placement:** one file per feature, in the `architecture/` folder of
   the app it belongs to (for example `architecture/ifi_home_app/events.md`).
   A feature gets its own folder only when it grows past one file. Create
   an app folder when you write its first doc, not before.
2. **Cross-app features and `core_app`** go in `architecture/shared/`.
   Guides to how the project uses a framework or tool across the whole
   site (templates and CSS, Wagtail) go directly in `architecture/`.
3. **README next to the code, or here?** A `README.md` inside a code
   folder (such as `ifiplatform/templates/`) covers only that folder and
   links here for the bigger picture. How things work together belongs in
   `docs/`.
4. **Developers or editors?** `architecture/` is for developers. How-tos
   for editors, such as setting up a menu in the Wagtail admin, go in
   `contributing/content_guide.md`.
5. **These docs are the source of truth.** Never link to
   `claude_context/` from a doc for people. Only the main README may link
   to `claude_references/`. You may use the claude notes as source
   material, but rewrite what you take for people.
6. **Keep the overview current:** a PR that adds an app, a page type or an
   external service also updates
   [architecture/overview.md](architecture/overview.md).
7. **Dates:** every doc in `docs/` starts with `Last updated: YYYY-MM-DD`
   under its title. Change the date whenever you change the content.

## Planned docs

Docs the project is missing, most important first. When you write one,
tick it off here and add it to its folder's list above in the same PR.

### Operations: do these first

These are the risky gaps. If the server is lost or the maintainer leaves,
nobody can recover without them.

- [x] `operations/backups_and_recovery.md`: what is backed up (PostgreSQL
  and `media/`), how often, where the copies are stored *outside* the VM,
  and step-by-step restore. Test a restore at least once.
- [x] `operations/server_setup.md`: how to rebuild the server from zero:
  packages, PostgreSQL user and database, venv, `.env`, `gunicorn.service`,
  the Nginx site config, Certbot, fail2ban jails, sudo scope and NREC
  security groups. Consider also checking these config files into `deploy/`.
- [ ] `operations/access_and_handover.md`: who has access to what (NREC
  project, SSH keys, GitHub admin and secrets, domain/DNS, DeepL, Umami,
  Peoply, email) and how to add or remove a person.
- [ ] `operations/incidents.md`: what to do when production breaks:
  rolling back a bad deploy, pausing the nightly deploy, who to tell.
- [ ] `SECURITY.md` (repo root): how to report a security problem
  privately. GitHub shows it on the repo's Security tab.

### Community and governance

- [ ] `CODE_OF_CONDUCT.md` (repo root): expected behaviour, and who
  handles reports.
- [ ] `GOVERNANCE.md` (repo root): the roles (moved from CONTRIBUTING.md),
  how someone becomes Collaborator or Committer, how decisions are made,
  and what happens when the current maintainers leave.
- [ ] `contributing/code_review.md`: checklist and tone for reviewers, and
  what a PR needs before it can be approved.
- [ ] `contributing/content_guide.md`: for non-developers: writing and
  translating articles in the Wagtail admin, setting up menus, editor
  terms, images.
- [ ] `contributing/writing_docs.md`: finished version of the AI draft
  `claude_references/writing_guidelines.md`.
- [ ] Finished version of the AI draft `claude_references/community_goals.md`,
  either in the main README's "About" section or as its own doc.
- [x] `.github/pull_request_template.md`: what changed, why, linked
  issue, how it was tested. There are issue templates but no PR template.

### Developer guides

- [x] `architecture/overview.md`: how the apps and the Wagtail page tree
  fit together, the main models, and the path from request to view to
  template.
- [ ] `architecture/wagtail.md`: how this project uses Wagtail:
  pages vs snippets vs plain Django models, the page tree and
  `subpage_types`, StreamField blocks, locales, `wagtail_hooks.py`, and how
  to add a new page type from start to finish. Also why an app prefix
  hides a page with the same slug, and why the hub page is never shown on
  its own.
- [ ] `architecture/shared/translations.md`: the Norwegian/English workflow
  end to end: wagtail-localize, DeepL and its glossary,
  `makemessages`/`compilemessages`, locale aliases.
- [ ] `architecture/shared/background_jobs.md`: the jobs that run outside
  a web request: the Peoply event sync (a systemd timer), the DeepL
  glossary sync (run by hand), and cleanup of unverified accounts (meant to
  run on a schedule, but nothing schedules it yet). Cover how each one runs,
  how often, where it logs, and what to do when one fails.
- [x] `architecture/ifi_home_app/articles.md`: article, category and index
  pages, StreamField blocks, and article and block styles.
- [x] `architecture/ifi_home_app/unions_and_tools.md`: student union and
  tool pages.
- [x] `architecture/ifi_home_app/events.md`: event pages, the calendar and
  the Peoply sync.
- [x] `architecture/ifi_home_app/menus.md`: how menus are modelled and
  rendered.
- [ ] `architecture/account_app/accounts.md`: sign-up, email verification,
  profiles and editor terms, and how `EditorTermsGateMiddleware` enforces
  them.
- [ ] `architecture/study_app/flashcards.md`: decks and cards.
- [ ] `contributing/testing.md`: running tests, writing new ones, and
  adding a new app to the test list in `ci.yml`.
- [ ] `operations/privacy_and_data.md`: which personal data is stored,
  where, and for how long (for example, unverified accounts are deleted
  after 7 days), and how to handle a deletion request. Backs up the public
  privacy policy page.

### Small fixes to existing docs

- [x] [CONTRIBUTING.md](../CONTRIBUTING.md): add a contact email.
- [x] [TUTORIALS.md](../TUTORIALS.md): add Wagtail and PostgreSQL
  resources (also added Git/GitHub and Docker).
