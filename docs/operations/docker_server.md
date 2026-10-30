# Docker server

Last updated: 2026-10-30

How to set up and run a server with Docker. Today this runs the Halloween
mock site. The real site (`ifiplattform.no`) still runs the old setup in
[prod_server.md](prod_server.md) and [server_setup.md](server_setup.md)
until it moves over.

This setup is for **servers only**. Local development uses the dev Docker
setup in [contributing/docker_guide.md](../contributing/docker_guide.md). Never run
this one on your own computer (see [HTTPS and HSTS](#https-and-hsts)).

## How it works

The server runs three containers, described in `compose.prod.yml` in the
repo root:

| Container | What it does |
| --------- | ------------ |
| `caddy` | The only one open to the internet (ports 80 and 443). Gets and renews the HTTPS certificate by itself, serves uploaded files (`/media/`), and passes everything else to `web` |
| `web` | Gunicorn running Django. The CSS/JS is built into its image and served by WhiteNoise. No open port: only Caddy can reach it |
| `db` | PostgreSQL 16. No open port |

The data lives in Docker **volumes**, which survive restarts and rebuilds:
`pgdata` (the database), `media` (uploaded files), `cache` (Django's
cache), `caddy_data` (the certificates).

The only things installed on the server itself are Docker and fail2ban.

### Where settings live

| File | Holds | In git? |
| ---- | ----- | ------- |
| `compose.prod.yml`, `Dockerfile`, `deploy/docker/Caddyfile` | What is the same on every server: how the containers are built and connected | Yes |
| `.env` in the repo root | What is different on each server, or secret: domain, passwords, secret key | Never |

The template for `.env` is `deploy/docker/.env.example`. It also lists the
settings the compose file fills in by itself. To see the final values
every container gets, run `docker compose config`.

## Setting up a new server

1. **Create the VM in NREC:** Ubuntu 24.04, `m1.medium`, network
   `dualStack`, your SSH key, and a security group that opens only ports
   22, 80 and 443.
2. **Add a DNS record** for the site's address, pointing at the VM's IPv4
   address. The domain's DNS is managed at Gigahost. Add a record with
   type `A`, the name (for example `halloween`) and the IP, with TTL 300.
   Leave the existing records alone. An `AAAA` record for IPv6 is
   optional, but if you add one it must be correct, or the site breaks
   for IPv6 visitors.
3. **Log in and get the code:**
   ```bash
   ssh ubuntu@<server-ip>
   git clone <repo URL>
   cd <repo folder>
   ```
4. **Prepare the server:** installs Docker and fail2ban, adds swap and
   moves the automatic security updates to 04:00.
   ```bash
   sudo bash deploy/docker/setup_server.sh
   ```
   Then **log out and back in**, so you can use `docker` without `sudo`.
5. **Fill in the settings:**
   ```bash
   cp deploy/docker/.env.example .env
   chmod 600 .env        # only you can read the secrets
   nano .env
   ```
   Follow the comments in the file. `DJANGO_SECRET_KEY` and
   `DB_PASSWORD` must be new random values, never copied from another
   server. On the mock site, keep `OPEN_SIGNUP=True` (see
   [Open sign-up](#open-sign-up-mock-site-only)).
6. **Check that DNS works** from your own computer:
   `nslookup <the site's address>` should show the server's IP. Caddy
   can't get a certificate before it does.
7. **Start the site:**
   ```bash
   bash deploy/docker/deploy.sh
   ```
   The first run takes a few minutes: it builds the image, creates the
   database and gets the certificate.
8. **Create an admin login:**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
9. **Open the site** in a browser and check the padlock, the styling and
   the images.

From now on the site stays up by itself. Docker restarts a container
that crashes and starts everything again after a reboot, and Caddy renews
the certificate.

## Deploying new code

Every merge into `main` deploys by itself. The GitHub Actions workflow
`.github/workflows/deploy.yml` runs the tests and lint, then logs in to
the server over SSH and runs the deploy script. To deploy without a
merge, start it by hand: Actions tab, "Deploy", "Run workflow". The
`skip_ci` option there skips the tests, for emergencies only.

The workflow needs three secrets in the repo (Settings, Secrets and
variables, Actions):

| Secret | Value |
| ------ | ----- |
| `SERVER_IP` | The server's IPv4 address |
| `SERVER_USER` | `ubuntu` |
| `SSH_PRIVATE_KEY` | A private key whose public key is in the server's `~/.ssh/authorized_keys`. Make a new key just for this, not your own |

The workflow expects the repo at `/home/ubuntu/ifiplattform_halloween`.
If you clone it somewhere else, change the `cd` line in the workflow.

To deploy by hand on the server, **always use the script:**

```bash
bash deploy/docker/deploy.sh
```

It pulls the newest code from the branch in `DEPLOY_BRANCH`, builds a new
image, migrates the database, runs `SEED_COMMAND` if set, swaps in the new
containers and clears the cache. The site shows "502" for a few seconds
while the new `web` container starts.

Don't update by hand with `git pull` and `docker compose up`. That skips
the migrations, and the site breaks on the first change that needs one.

The script runs in two parts: it pulls the code, then restarts itself
from the new copy (`--after-reset`). That way a change to `deploy.sh`
takes effect in the same deploy.

To roll back a bad deploy, revert the commit on GitHub and deploy again.

## Open sign-up (mock site only)

`OPEN_SIGNUP=True` in `.env` makes it easy for event participants to get
in, and keeps personal data off a server we can't promise to keep safe:

- Signing up asks only for a username and password. No email, no name,
  and no verification email.
- Every new account is logged in at once and joins Wagtail's
  **Moderators** group, so it can write, edit and publish pages and
  upload images. It can't manage users or site settings.
- There are no content-ownership terms to accept before using the
  Wagtail admin or the editor mode on pages.
- Instead of the real privacy policy there is a short **event privacy
  notice** (same address and links). It says what is stored and public,
  and that the site is deleted no later than 2 November 2026. Fill in the
  contact address in `account_app/templates/legal/event_privacy_notice.html`
  before the event.
- The account page hides the email and name fields.

Leave `OPEN_SIGNUP` out of `.env`, or set it to `False`, on the real site.
That gives the normal sign-up with email verification, the privacy policy
and the terms.

If you created `.env` before this setting existed, add the line
`OPEN_SIGNUP=True` by hand and run `docker compose up -d` to restart
with it. Don't copy `.env.example` over `.env` again: that deletes your
secrets.

## Points, leaderboard and helper solutions

The mock site counts points for the event. Three public pages, all under
`/commits/`:

- **My issues** (`/commits/`, needs a login): a participant enters their
  GitHub username once and sees their points and drink-ticket progress.
  The site menu still calls the whole section "Commits".
- **Leaderboard** (`/commits/leaderboard/`): reloads itself every 30
  seconds, so it can stay on the projector.
- **Issues** (`/commits/issues/`): every event issue, free or done.
  Clicking an issue opens it in a pop-up with more details (who solved it,
  the PR, the issue it is part of). Each issue also has its own page,
  `/commits/issues/<number>/`, for sharing a link. Participants claim
  issues here (see "Claiming issues" below).

### Claiming issues

Participants don't comment on GitHub or wait for a helper. On the Issues
page they press **Claim** on a free card. Or they press **🎲 Give me an
issue**: it opens a random free issue of the difficulty and category they
picked, in the same pop-up as a clicked card, where they can **Claim** it
or press **Try another**. Nothing is claimed until they press Claim. The
rules are in `ifiplatform/apps/commits_app/claims.py`.

- You need a linked GitHub username (on My issues) to claim.
- An issue is free when it's open, worth points, not claimed, and not
  assigned on GitHub. Only one person can win a claim, even if two press
  at the same moment; the other is offered a similar free issue.
- Each person can hold 2 open issues (`CLAIM_LIMIT` in `settings.py`),
  counting both their claims and issues assigned to them on GitHub.
- A claim runs out if nothing happens: 30 minutes for 🍬, 60 for 🍫, 90
  for 🎃 (`CLAIM_MINUTES`). The claimer can press **Keep** for the full
  time again. Once the sync sees an open pull request by the claimer,
  their claims have no time limit.
- Everyone sees their issues in their own shuffled order, free ones
  first, so not everyone goes for the same first card.
- A newly claimed issue is outlined with a **new** badge on My issues
  until the participant opens it for the first time.

Helpers, in an issue's pop-up, see who holds the claim and can give
**+15 min**, **+30 min**, **No time limit** or **Reset**, and
**Force release** it (also with a pull request open). Organisers can also
release claims in `/admin/` → Commits → Claims ("Release selected
claims"). Claims on closed issues can't be released: they decide the
points.

Two things helpers should do:

- **Close the issue when you merge** its pull request, unless the PR said
  "Closes #12" (then GitHub closes it). The points arrive when the issue
  closes, and until then the claim counts toward the participant's limit.
- **Force-release before you assign someone else on GitHub.** A claim
  wins over a GitHub assignee for the points.

### Where the points come from

The site reads the event repo on GitHub. Nobody reports anything by hand.

- An issue counts if it has a size label: `🍬 candy`, `🍫 chocolate` or
  `🎃 pumpkin`. Each size gives **coins** (1, 2, 3), which count towards
  the drink ticket, and **contest points** (0, 2, 3), which decide the
  leaderboard and its top 3. Candy gives no points on purpose, so nobody
  climbs the leaderboard with the beginners' issues. The names and values
  are in `SIZE_LABELS` and `CONTEST_POINTS` in
  `ifiplatform/apps/commits_app/labels.py`.
- When a **claimed** issue is closed as completed, the person who claimed
  it gets the points, however it was closed. Nobody needs to write
  "Closes #12".
- For an issue nobody claimed: when a merged PR closes it ("Closes #12" in
  the PR), its author gets the points. An issue closed without a PR, such
  as a content issue, gives the points to the first person **assigned**
  to it, so assign them before you close it.
- A PR that closes more than one unclaimed event issue earns none of
  them. The leaderboard shows those issues to organisers under "Needs a
  look".
- To fix credit by hand (the wrong person got it), add a **credit
  override** in `/admin/` → Commits →
  Credit overrides: the issue number and the right GitHub username. It
  wins over everything else and survives later syncs.

The site stores only public GitHub data: usernames, issue and PR numbers,
titles and labels. Never names, emails or profile pictures.

### The GitHub token

The sync needs a read-only token in `.env`:

1. On GitHub: Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token. Under "Repository access"
   choose **Public repositories (read-only)**. Give it no other
   permissions, and an expiry date after the event.
2. Put it in `.env` as `GITHUB_READ_TOKEN=...` and run
   `docker compose up -d` to restart with it.

Without a token the points never update, and the leaderboard warns
organisers. Revoke the token after the event.

### When it syncs

- After every deploy (the last step of `deploy.sh`).
- When someone opens the leaderboard or the issue list, at most once a
  minute.
- When a helper or organiser presses **Sync now**, at the left of the
  tab bar on every Commits page.

By hand: `docker compose exec web python manage.py sync_github_points`.
If GitHub is down, the site keeps the points it already has.

### Organisers and helpers

- **Organisers** are site users with "staff status" or superusers. On the
  leaderboard they see warnings and a **Handed out**
  button for everyone who has earned a drink ticket
  (`DRINK_TICKET_COINS` in `settings.py`, 5 coins). The podium shows
  only people with points; everyone else is listed below it.
- **Helpers** get a solution button on every issue card. It opens the
  issue with its solution, or says "Solution missing" if none was loaded
  for that issue. They also have **Sync now** in the tab bar, and see
  the GitHub usernames of contributors who haven't linked an account yet. To
  make someone a helper: they sign up on the site, then in `/admin/` →
  Users → their user → Groups, add **Helpers** and save.

### Loading the solutions

The solutions file is private: never commit it. It is a JSON list:

```json
[{"issue": 12, "note": "Change the colour in footer.css...", "diff": "- old\n+ new"}]
```

Load it from your own computer:

```bash
ssh ubuntu@<server-ip> "cd ifiplattform_halloween && docker compose exec -T web python manage.py load_event_solutions" < solutions.json
```

Running it again updates the solutions instead of adding copies.

## After the event

The privacy notice promises that the mock site is deleted no later than
**2 November 2026**. A timer on the server wipes it at 09:00 that day.

By 1 November:

Take nothing off the site that is about a person: no leaderboard
screenshots, no database copies. Only the anonymous totals.

1. Take the anonymous totals:
   `docker compose exec -T web python manage.py halloween_totals > halloween_totals.csv`.
   Fill in the empty rows by hand, move the file off the server, and
   delete the copy there.
2. Disable the deploy workflow (GitHub → Actions → Deploy → Disable
   workflow). Otherwise a push brings the site back up with an empty
   database.
3. Try the wipe: `sudo bash deploy/halloween/wipe_mock_site.sh --dry-run`.
   If it fails, fix that first and don't install the timer.
4. Install the timer:

   ```bash
   sudo cp deploy/halloween/halloween-wipe.service deploy/halloween/halloween-wipe.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now halloween-wipe.timer
   systemctl list-timers halloween-wipe.timer   # should show 2 November 09:00
   ```

On 2 November, after 09:00:

1. Check the wipe: `journalctl -u halloween-wipe` ends with "Wipe
   complete." If a step failed, fix it and run the script again by hand.
   It stops the timers, removes the containers and volumes (database,
   uploads, logs), deletes any backups and then `.env`.
2. Delete the VM, its disks and any snapshots in NREC.
3. Remove the `halloween` DNS record at Gigahost.
4. Revoke the GitHub token (GitHub → Settings → Developer settings →
   Personal access tokens), and delete the deploy secrets in GitHub
   Actions and the `.env` copy in your password manager.

## Everyday commands

Run them from the repo folder on the server.

| You want to… | Command |
| ------------ | ------- |
| See what's running | `docker compose ps` |
| Follow Django's log | `docker compose logs -f web` |
| See Caddy's log (requests, certificates) | `docker compose logs caddy` |
| Restart everything (same code) | `docker compose restart` |
| Run a Django command | `docker compose exec web python manage.py <command>` |
| Open a Django shell | `docker compose exec web python manage.py shell` |
| Open the database | `docker compose exec db psql -U <DB_USER> -d <DB_NAME>` |
| See the final settings | `docker compose config` |

`restart` is safe at any time: it starts the same image again, so there
is nothing new to migrate.

## Things never to do

- **Change `postgres:16` to a newer major version** in `compose.prod.yml`
  without a dump and restore. PostgreSQL can't read another major
  version's data files, and the database won't start.
- **Change `DB_PASSWORD` in `.env` alone.** PostgreSQL only reads it the
  first time it creates the database. Change it inside the database too
  (the command is in `.env.example`).
- **Delete volumes** (`docker compose down -v`, `docker volume rm`). That
  deletes the database or the uploaded files.
- **Commit `.env`**, or copy its secrets into the repo.

## HTTPS and HSTS

With `DEBUG=False`, Django tells browsers: "for a year, use only HTTPS for
this domain and all its subdomains" (HSTS). Browsers remember this, and
the server can't take it back. So:

- **Every `*.ifiplattform.no` address must have HTTPS.** Caddy handles
  that, but a test server on plain HTTP under our domain won't open for
  anyone who has visited the main site.
- **Don't submit the domain to the HSTS preload list** (hstspreload.org).
  It makes the rule permanent and is very slow to undo.
- **A certificate error takes the site down.** Visitors can't click past
  it. If Caddy can't get or renew a certificate (wrong DNS, port 80
  blocked, Let's Encrypt limits), check `docker compose logs caddy` first.
- **Don't run this setup on `localhost`.** The browser would remember
  "localhost is HTTPS-only" and break the dev setup at
  `http://localhost:8000`.

## fail2ban

fail2ban bans IP addresses that fail to log in over SSH too many times
(5 tries in 10 minutes, banned for 1 hour). The rules are in
`deploy/docker/fail2ban/jail.local`. `setup_server.sh` installs them, and
running it again installs a changed version.

| You want to… | Command |
| ------------ | ------- |
| See who is banned | `sudo fail2ban-client status sshd` |
| Unban someone | `sudo fail2ban-client set sshd unbanip <ip>` |

There is no rule for the website. Bots looking for software we don't run
(`/wp-admin`, `/phpmyadmin`) only get "404 Not found". Banning them would
need Caddy on the server's own network and a custom log filter, which is a
lot to maintain for little protection. Password guessing on the Wagtail
login isn't covered by fail2ban either. If it's needed, it belongs in
Django (for example `django-axes`).

## When something goes wrong

| What you see | Look at |
| ------------ | ------- |
| Certificate error, or the site doesn't open at all | `docker compose logs caddy`. Usually DNS doesn't point at the server yet, or port 80 is closed in the security group |
| "502 Bad Gateway" for more than a minute | `docker compose logs web`. Django didn't start, often a missing or wrong value in `.env` |
| "Too many redirects" | `docker compose config`: `web` must have `FORWARDED_ALLOW_IPS: '*'` |
| "password authentication failed" in the `web` log | `DB_PASSWORD` was changed in `.env` after the database was created (see [Things never to do](#things-never-to-do)) |
| "403 CSRF verification failed" when logging in | `SITE_DOMAIN` in `.env` doesn't match the address in the browser |
| Pages without styling | `docker compose logs web`. The build's `collectstatic` step is in the `Dockerfile` |
| The disk is full | `df -h` and `docker system df`. The deploy deletes old images, but check for large logs and uploads |
