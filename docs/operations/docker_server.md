# Docker server

Last updated: 2026-10-14

How to set up and run a server with Docker. Today this runs the Halloween
mock site. The real site (`ifiplattform.no`) still runs the old setup in
[prod_server.md](prod_server.md) and [server_setup.md](server_setup.md)
until it moves over.

This setup is for **servers only**. Local development uses the dev Docker
setup in [contributing/docker.md](../contributing/docker.md). Never run
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
   server.
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

**Always deploy with the script:**

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
