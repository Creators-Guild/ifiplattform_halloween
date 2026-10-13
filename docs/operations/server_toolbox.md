# Server toolbox

Last updated: 2026-09-29

The tools you use to find out what's going on with the production server,
and how to use them. The goal is to teach the tools, not just list fixed
commands, so that when something new goes wrong you know where to look,
what to search for, and what to ask.

For what runs on the server and how it's set up, read
[prod_server.md](prod_server.md) first.

## The big picture

- **systemd** is the program that starts and supervises everything on the
  server: Gunicorn (the Django app), Nginx, PostgreSQL, fail2ban, the
  Peoply sync timer and the backup timer. Each of these is called a **unit**. You control units
  with `systemctl`.
- Everything a unit prints goes into the **journal**, systemd's central log.
  You read it with `journalctl`.
- **Django errors end up in the Gunicorn journal.** With `DEBUG` off,
  `settings.py` sends errors to standard output, and systemd stores that in
  the journal for `gunicorn`.
- **Nginx** is the exception: it writes its own log files in
  `/var/log/nginx/`.

So for almost any problem, the question is: *which unit is involved, and
what does its log say?*

## Where do I look?

| Symptom                                   | Look here first                                                                   |
| ----------------------------------------- | --------------------------------------------------------------------------------- |
| Site doesn't load / "502 Bad Gateway"     | `systemctl status gunicorn`, then `journalctl -u gunicorn -e`. Nginx is up, but Gunicorn behind it isn't answering |
| "500 Server Error" on a page              | `journalctl -u gunicorn --since "10 min ago"`. The Python traceback is there       |
| CSS or images missing (404)               | Did `collectstatic` run in the deploy? Then `sudo tail /var/log/nginx/error.log`   |
| Browser warns about the certificate       | `sudo certbot certificates` and `sudo certbot renew --dry-run`                     |
| Events from Peoply not updating           | `systemctl list-timers` and `journalctl -u sync-peoply-events -e`                  |
| Backups missing or old                    | `journalctl -u ifiplatform-backup -e`, see [backups_and_recovery.md](backups_and_recovery.md#checking-that-it-runs) |
| Can't SSH in                              | Your IP may be banned by fail2ban (see [fail2ban](#fail2ban)), or the NREC security group changed |
| Deploy failed                             | The failed run in GitHub → Actions → Deploy. Its log shows the server's output     |
| Site is slow or processes are crashing    | `free -h`, `top` and `df -h` (see [Resources](#resources-disk-memory-cpu))         |

## journalctl: reading logs

`journalctl` shows the journal. Used on its own it shows *everything* from
the whole system, which is far too much, so you almost always narrow it
down with flags. Flags can be combined freely.

### Choosing what to see

| Flag                          | Meaning                                              | Example                                       |
| ----------------------------- | ---------------------------------------------------- | --------------------------------------------- |
| `-u <unit>`                   | Only this unit                                        | `journalctl -u gunicorn`                      |
| `-n <N>`                      | Only the last N lines                                 | `journalctl -u gunicorn -n 50`                |
| `-e`                          | Open at the **end** (newest) instead of the start     | `journalctl -u gunicorn -e`                   |
| `-r`                          | **Reverse**: newest first                             | `journalctl -u nginx -r`                      |
| `-f`                          | **Follow**: keep showing new lines live, Ctrl+C to stop | `journalctl -u gunicorn -f`                 |
| `--since` / `--until`         | Time window                                           | `--since "1 hour ago"`, `--since today`, `--since "2026-09-28 14:00" --until "2026-09-28 15:00"` |
| `-b`                          | Only since the last reboot                            | `journalctl -u postgresql -b`                 |
| `-p <level>`                  | Only this priority or worse (`err`, `warning`, …)     | `journalctl -p err -b`                        |
| `--no-pager`                  | Print straight to the terminal, for piping to `grep`  | `journalctl -u gunicorn --no-pager`           |

A note on `-p err`: it's good for system services, but **not for Django**.
Everything Gunicorn prints, errors included, is stored at the normal "info"
level. To find Django errors, search the text instead (see below).

### Common combinations

```bash
journalctl -u gunicorn -f                                   # watch live while you reproduce a bug in the browser
journalctl -u gunicorn --since "30 min ago"                 # what happened recently
journalctl -u gunicorn --since today --no-pager | grep -i -A 20 "error"   # every error today, with 20 lines after each
journalctl -u sync-peoply-events -n 100                     # last Peoply sync runs
journalctl -p err -b                                        # all serious errors from any service since boot
```

`grep -i "text"` keeps only lines containing the text, ignoring case.
`-A 20` also shows the 20 lines **A**fter each match, which is where a
Python traceback continues. (`-B` shows lines **B**efore, `-C` both.)

### Moving around inside the log

Without `--no-pager`, journalctl opens the log in a *pager* (the program
`less`) so you can scroll:

| Key             | Does                               |
| --------------- | ---------------------------------- |
| `q`             | Quit                               |
| ↑ ↓ / PgUp PgDn | Scroll                             |
| `G` / `g`       | Jump to the end / the start        |
| `/text` Enter   | Search forward for "text"          |
| `n` / `N`       | Next / previous search match       |

### Keeping the journal small

The journal takes up disk space too, which matters on a 20 GB disk:

```bash
journalctl --disk-usage                    # how much space the logs use
sudo journalctl --vacuum-time=2weeks       # delete logs older than two weeks
```

If journalctl says there are no entries, or that you can't see all the
logs, run it with `sudo`.

## systemctl: controlling services

`systemctl` starts, stops and inspects units.

```bash
systemctl status gunicorn            # is it running? plus its last few log lines
sudo systemctl restart gunicorn      # stop + start: loads new code or a changed .env
sudo systemctl stop gunicorn         # stop now (the site goes down)
sudo systemctl start gunicorn        # start now
sudo systemctl reload nginx          # re-read config without dropping connections
systemctl is-active gunicorn         # prints just "active" or "inactive"
systemctl --failed                   # every unit that has crashed
systemctl list-timers                # scheduled jobs and when they run next
systemctl cat gunicorn               # show the unit file (how it's started, as which user)
sudo systemctl daemon-reload         # needed after editing a unit file
```

### Reading `systemctl status`

```
● gunicorn.service - gunicorn daemon
     Loaded: loaded (/etc/systemd/system/gunicorn.service; enabled; ...)
     Active: active (running) since Mon 2026-09-28 01:12:03 UTC; 3h ago
   Main PID: 12345 (gunicorn)
     ...
Sep 28 01:12:03 ... Booting worker with pid: 12346
```

- **Loaded**: where the unit file is, and `enabled` means it starts
  automatically on boot.
- **Active**: the key line. `active (running)` is good. `failed` or
  `inactive (dead)` means it's down. The time tells you how long it's been
  in that state; a very recent time can mean it keeps crashing and
  restarting.
- The lines at the bottom are the last few journal entries. For more, use
  `journalctl -u <unit>`.

### restart vs reload, start vs enable

- **restart** fully stops and starts the service: a short outage, but
  everything is reloaded. **reload** asks the service to re-read its config
  without stopping. Nginx supports reload. For Gunicorn, use restart.
- **start/stop** act *now*. **enable/disable** decide whether it starts
  *at boot*. `enable --now` does both.

## Nginx

```bash
sudo tail -n 50 /var/log/nginx/error.log      # last 50 lines
sudo tail -f /var/log/nginx/error.log         # follow live, Ctrl+C to stop
sudo tail -f /var/log/nginx/access.log        # every request as it happens
sudo grep " 404 " /var/log/nginx/access.log | tail -n 20   # recent "not found" requests
sudo nginx -t                                 # test the config for mistakes
sudo systemctl reload nginx                   # apply config changes
```

- `access.log` has one line per request: IP, time, URL, status code
  (200 OK, 404 not found, 502 backend down, …). `error.log` has problems
  Nginx itself ran into, such as not reaching Gunicorn or a missing file.
- The site config lives in `/etc/nginx/sites-available/`. It's switched on
  by a link to it from `/etc/nginx/sites-enabled/`.
- **Always run `sudo nginx -t` before reloading.** If the config is broken,
  a reload is refused and the site keeps running on the old config. A
  restart with a broken config would take the site down.
- Older logs are rotated to `error.log.1`, `error.log.2.gz` and so on. Use
  `zcat` or `zgrep` to read the `.gz` ones.

## Django and manage.py on the server

Always get into the right folder and activate the virtualenv first,
otherwise `python` won't find Django or the `.env`:

```bash
cd /home/ubuntu/IfiPlatform/ifiplatform
source ../venv/bin/activate
```

Then:

```bash
python manage.py check --deploy          # Django's own production-settings checklist
python manage.py showmigrations          # which migrations are applied ([X]) or not ([ ])
python manage.py shell                   # Python prompt with the project loaded, to inspect data
python manage.py createsuperuser         # new admin user
python manage.py sync_peoply_events      # run the Peoply sync by hand
```

All of this project's own commands are in
[management_commands.md](management_commands.md).

`shell` works on the **live database**. Reading is safe; anything that
saves or deletes is permanent.

## PostgreSQL

```bash
sudo -u postgres psql                    # open the database prompt as the postgres admin user
```

Inside `psql`:

| Command       | Does                                      |
| ------------- | ----------------------------------------- |
| `\l`          | List databases                            |
| `\c <name>`   | Connect to one (the name is `DB_NAME` in `.env`) |
| `\dt`         | List tables                               |
| `\d <table>`  | Show a table's columns                    |
| `\q`          | Quit                                      |

Before anything risky (a tricky migration, manual data fixes), take a
backup:

```bash
bash /home/ubuntu/IfiPlatform/deploy/backup/backup_db.sh
```

How to restore one: [backups_and_recovery.md](backups_and_recovery.md).

## fail2ban

fail2ban watches the logs and blocks IP addresses that fail to log in over
SSH too many times, or that probe Nginx for known weak spots. Each rule set
is called a **jail**.

```bash
sudo fail2ban-client status                       # list jails
sudo fail2ban-client status sshd                  # banned IPs in the SSH jail
sudo fail2ban-client set sshd unbanip <ip>        # remove a ban
```

If *you* get banned, you can't SSH in from that IP. Unban yourself from
another network (mobile hotspot) or through the console in the NREC
dashboard.

## Resources: disk, memory, CPU

The VM is small (1 vCPU, 4 GB RAM, 20 GB disk), so running out of
something is a realistic cause of odd problems.

```bash
df -h                                                  # free space per disk; worry above ~85 % on /
du -sh /home/ubuntu/IfiPlatform/ifiplatform/* | sort -h    # which folders are biggest (media/ is a usual suspect)
sudo du -sh /var/log/* | sort -h                       # big log files
free -h                                                # memory; look at "available"
uptime                                                 # load average; above ~1.0 means the single CPU is busy
top                                                    # live list of processes, q to quit (htop is nicer if installed)
```

`-h` on these commands means **h**uman-readable sizes (MB/GB instead of
bytes).

## Getting unstuck

When something new happens that this doc doesn't cover:

1. **Find the exact error.** Use the table in
   [Where do I look?](#where-do-i-look) to pick the right log, and copy
   the exact error line, not a paraphrase.
2. **Learn the tool.** `man journalctl` is the full manual, `journalctl --help`
   is the short version, and `tldr journalctl` (if installed) gives
   everyday examples. This works for any command.
3. **Search well.** Combine the tool, the exact error text and the
   context, for example: `gunicorn "Worker failed to boot" django`, or
   `nginx "connect() failed (111: Connection refused)" ubuntu 24.04`.
4. **Asking an AI.** Give it the command you ran, the full error output and
   the relevant log lines, plus the setup: *Ubuntu 24.04, Nginx → Gunicorn
   → Django 6 + Wagtail, PostgreSQL, systemd*. **Never paste the contents
   of `.env`, passwords, keys or the server's IP address.**
5. **Before you change anything, know how to undo it.** Test Nginx config
   with `nginx -t`. Run the backup script before touching the database. Prefer
   reload over restart. Anything you edit in the code on the server must be
   committed and pushed, or the next deploy removes it (see
   [prod_server.md](prod_server.md#layout-on-disk)).
