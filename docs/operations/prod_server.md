# Production server

Last updated: 2026-09-29

How the live IfiPlatform site is hosted, deployed and secured. For the
software itself, see [architecture/tech_stack.md](../architecture/tech_stack.md).

Access details (IP address, SSH user and key) are deliberately not in this
public repo. Ask a maintainer if you need server access.

## Host

| Item      | Value                                                        |
| --------- | ------------------------------------------------------------ |
| Provider  | NREC (Norwegian Research and Education Cloud)                |
| OS        | Ubuntu 24.04 LTS                                             |
| Flavor    | `m1.medium`: 1 vCPU, 4 GB RAM, 20 GB disk                    |
| Services  | Nginx, Gunicorn, PostgreSQL and fail2ban, all on this one VM |

## How a request is served

```
Browser ──HTTPS──▶ Nginx ──▶ Gunicorn ──▶ Django / Wagtail ──▶ PostgreSQL
                    │
                    └── serves /static/ and /media/ directly from disk
```

- **Nginx** is the reverse proxy. It ends HTTPS (certificates from Let's
  Encrypt via Certbot) and serves static and media files itself, because
  Django doesn't serve them when `DEBUG` is off. Its site config lives on
  the server, with a copy in
  [deploy/server_config/](../../deploy/server_config/).
- **Gunicorn** runs the Django app (`ifiplatform_project.wsgi`) as the
  systemd service `gunicorn.service`.
- **PostgreSQL** runs locally on the same VM.

## Layout on disk

```
/home/ubuntu/IfiPlatform/            the git checkout (always equal to origin/main)
├── venv/                            Python virtualenv
├── deploy/                          deploy.sh, backup script, systemd units, config copies
└── ifiplatform/                     Django project (manage.py lives here)
    ├── .env                         secrets and settings, gitignored
    ├── staticfiles/                 output of collectstatic, served by Nginx
    ├── media/                       user uploads (Wagtail images, documents)
    └── django_cache/                file-based cache shared by Gunicorn workers

/mnt/backups/                        separate NREC volume for backups
├── postgres/                        database dumps
└── media/                           media/ archives
```

How the backups work and how to restore them:
[backups_and_recovery.md](backups_and_recovery.md). How to rebuild the
whole server: [server_setup.md](server_setup.md).

The checkout is reset to `origin/main` on every deploy, and any change that
isn't on `origin/main` by then is lost. Editing code directly on the server
is fine, but **commit and push it to `main` before the next deploy**
(nightly at 01:00 UTC). `.env`, `media/` and the database are not tracked
by git, so deploys leave them alone.

## systemd services and timers

| Unit                        | What it does                                                         | Defined in                  |
| --------------------------- | -------------------------------------------------------------------- | --------------------------- |
| `gunicorn.service`          | Runs the Django app                                                  | On the server, copy in [deploy/server_config/](../../deploy/server_config/) |
| `nginx.service`             | Reverse proxy and HTTPS                                              | Ubuntu package              |
| `postgresql.service`        | Database                                                             | Ubuntu package              |
| `fail2ban.service`          | Bans IPs after repeated failed logins or scans                       | Ubuntu package              |
| `sync-peoply-events.timer`  | Runs `sync_peoply_events` at 00/06/12/18:00 daily, plus 14:00 and 16:00 on weekdays | [deploy/systemd/](../../deploy/systemd/) |
| `ifiplatform-backup.timer`  | Backs up the database and `media/` daily at 05:00                    | [deploy/systemd/](../../deploy/systemd/) |

Unit files in `deploy/systemd/` are copied to `/etc/systemd/system/` and
enabled on every deploy, so you change them by editing the repo, not the
server.

## Environment variables

Set in `ifiplatform/.env` on the server. Only the key names are listed
here, never the values.

| Key                                                 | Purpose                                                      |
| --------------------------------------------------- | ------------------------------------------------------------ |
| `DJANGO_SECRET_KEY`                                 | Django's secret key                                          |
| `DEBUG`                                             | Must be `False` in production (turns on the security settings) |
| `DJANGO_ALLOWED_HOSTS`                              | Comma-separated hostnames the site answers to                |
| `CSRF_TRUSTED_ORIGINS`                              | Comma-separated `https://` origins trusted for forms         |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection                                  |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Outgoing email (console output if `EMAIL_HOST` is unset) |
| `DEEPL_API_KEY`                                     | DeepL machine translation                                    |
| `DEEPL_GLOSSARY_ID`                                 | Written automatically by `sync_deepl_glossary --write-env`   |
| `UMAMI_SCRIPT_URL`, `UMAMI_WEBSITE_ID`              | Umami analytics                                              |

After changing `.env` by hand, restart the app with
`sudo systemctl restart gunicorn`.

## Deploy flow

Deploys are **not** triggered by pushing to `main`. They run from
[.github/workflows/deploy.yml](../../.github/workflows/deploy.yml):

- **Nightly at 01:00 UTC.** Skipped if `main` hasn't changed since the last
  successful deploy.
- **By hand** from the Actions tab ("Run workflow"), with two optional
  switches:
  - `skip_ci`: deploy without running tests and lint first (emergencies only).
  - `skip_countdown`: skip the 10-minute visitor warning.

What happens:

1. **CI** ([ci.yml](../../.github/workflows/ci.yml)) runs tests and lint.
   The deploy stops if it fails.
2. GitHub Actions connects over SSH (`appleboy/ssh-action`), fetches
   `main`, and runs the newest [deploy/deploy.sh](../../deploy/deploy.sh).
3. `deploy.sh` then:
   1. Shows a "site is updating" banner to visitors (`announce_deploy`) and
      waits 10 minutes while the old code keeps serving.
   2. `git reset --hard origin/main`. A reset, never a merge, so the server
      can't end up with merge conflicts.
   3. Re-runs itself from the new code, so changes to `deploy.sh` take
      effect in the same deploy.
   4. Copies and enables the systemd units from `deploy/systemd/`.
   5. `pip install -r requirements.txt`
   6. Backs up the database and `media/` to `/mnt/backups` with
      [deploy/backup/backup_db.sh](../../deploy/backup/backup_db.sh). If
      the backup fails, the deploy stops here and nothing is migrated.
   7. `manage.py migrate`
   8. `manage.py collectstatic --noinput --clear`
   9. `manage.py sync_deepl_glossary --write-env`, but only if the glossary
      terms changed. A failure here only prints a warning.
   10. `sudo systemctl restart gunicorn`
   11. `manage.py clear_cache` and `announce_deploy --clear` to remove the
       banner.
   12. Compares the config copies in
       [deploy/server_config/](../../deploy/server_config/) with the live
       files on the server. Any difference shows up as a yellow warning on
       the run's page in GitHub Actions. It never fails the deploy.

Only one deploy can run at a time.

**If GitHub Actions is down,** SSH into the server and run the same script
by hand:

```bash
cd /home/ubuntu/IfiPlatform
bash deploy/deploy.sh
SKIP_COUNTDOWN=true bash deploy/deploy.sh   # without the 10-minute warning
```

## Security

- **SSH:** key-based login only, no passwords.
- **Firewall:** NREC security groups only allow ports 22 (SSH), 80 (HTTP)
  and 443 (HTTPS).
- **fail2ban:** jails for `sshd`, `nginx-http-auth` and `nginx-botsearch`.
- **HTTPS:** Let's Encrypt certificates via Certbot, which renews them
  automatically.
- **Django hardening:** active whenever `DEBUG` is off:
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and
  HSTS for one year, including subdomains and eligible for preload.
- **Hosts:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` come from `.env`,
  not from code.
- **Secrets:** only in `.env`, which is gitignored and never committed. The
  GitHub Actions deploy uses repository secrets for the server address,
  user and SSH key.
- **sudo:** the `ubuntu` user, which the deploy also logs in as, has
  passwordless sudo for **everything** (Ubuntu's cloud-init default, in
  `/etc/sudoers.d/90-cloud-init-users`). Anyone with the deploy SSH key
  therefore has full root access. The narrower rule in `/etc/sudoers`
  (only `systemctl restart gunicorn`) has no effect on top of that.

## Routine checks

What each of these tools does, and how to use them to track down new
problems, is explained in [server_toolbox.md](server_toolbox.md).

```bash
sudo certbot renew --dry-run        # certificate auto-renewal still works
systemctl status gunicorn nginx postgresql fail2ban
systemctl list-timers               # sync-peoply-events and ifiplatform-backup are scheduled
journalctl -u ifiplatform-backup -n 5   # last backups say "Backup completed"
journalctl -u gunicorn -n 100       # recent app errors (Django logs errors here)
journalctl -u sync-peoply-events    # last Peoply sync runs
sudo fail2ban-client status         # active jails and ban counts
df -h                               # disk space (the VM only has 20 GB)
```
