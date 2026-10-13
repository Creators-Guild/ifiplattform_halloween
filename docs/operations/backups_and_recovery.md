# Backups and recovery

Last updated: 2026-09-29

What is backed up on the production server, how to check that the
backups are working, and how to restore from them. For the server itself,
see [prod_server.md](prod_server.md). For the tools used here (`systemctl`,
`journalctl`, `psql`), see [server_toolbox.md](server_toolbox.md).

## Summary

| Item          | Value                                                                           |
| ------------- | ------------------------------------------------------------------------------- |
| What          | The PostgreSQL database and `media/` (uploaded images and documents)            |
| Script        | [deploy/backup/backup_db.sh](../../deploy/backup/backup_db.sh)                  |
| When          | Daily at 05:00 (`ifiplatform-backup.timer`), and before `migrate` in every deploy |
| Where         | `/mnt/backups/postgres/` and `/mnt/backups/media/`                              |
| Storage       | A separate 20 GiB NREC volume (`ifiplattform-backups`), not the VM's own disk   |
| Kept for      | 14 days                                                                         |
| Log           | `journalctl -u ifiplatform-backup` (the deploy's run is in the GitHub Actions log) |

Each run writes two files with the same timestamp:

```
/mnt/backups/postgres/<db_name>_20260929_050000.dump   database, pg_dump custom format
/mnt/backups/media/media_20260929_050000.tar.gz        the whole media/ folder
```

**They belong together.** Uploaded images and documents are Wagtail
Image and Document objects. The database stores each file's path, and the
file itself lives in `media/`. A database dump without its media archive
(or the other way round) leaves pages pointing at files that don't exist.
Always restore the `.dump` and the `.tar.gz` with the **same timestamp**.

## What is not covered

- **Copies outside NREC.** The backup volume survives a broken VM or a
  full disk, but not the NREC project being deleted or compromised. Copy
  backups out by hand for now, see
  [Copying backups outside NREC](#copying-backups-outside-nrec).
- **`.env`.** It holds secrets and is in no backup. If the VM is lost,
  every value has to be recreated or fetched from the service it belongs
  to (the key list is in
  [prod_server.md](prod_server.md#environment-variables)).
- **Server config.** The Nginx site, `gunicorn.service`, fail2ban and
  sudo rules live only on the server.
- **The code** is in git, so it doesn't need a backup.

## How the backup works

The script does this, and stops with an error if any step fails:

1. **Checks that `/mnt/backups` is mounted.** If the volume is missing,
   writing to `/mnt/backups` would quietly fill the VM's own 20 GB disk
   instead.
2. **Dumps the database to a `.tmp` file**, checks that `pg_restore -l`
   can read it, and only then renames it to `.dump`. A broken or half-written
   dump is never kept.
3. **Does the same for `media/`**: `tar` to a `.tmp` file, check it with
   `tar -tzf`, then rename.
4. **Deletes backups older than 14 days**, but only after a new backup
   has succeeded. If the backup keeps failing, the old ones stay.
5. Prints `Backup completed: <files>`.

It reads the database login from `ifiplatform/.env` (only the `DB_*`
keys).

**The volume.** `/mnt/backups` is mounted through `/etc/fstab` with the
`nofail` option, so the VM still boots if the volume is detached. In that
case the backup refuses to run (step 1) and the deploy stops before
`migrate`.

**Why 05:00.** Ubuntu's automatic upgrades run around 04:00 and can
briefly restart PostgreSQL. 05:00 stays clear of that.

**Why before every deploy.** Some migrations can't be undone. Their only
way back is a backup taken right before they ran. If that backup fails,
`deploy.sh` stops and nothing is migrated.

## Checking that it runs

Check this regularly, for example weekly. A backup job that nobody watches
can fail for a long time: from August 15 to September 21, 2026 every
backup failed with "Permission denied" because a folder was owned by
`root` while the job ran as `ubuntu`. Nobody noticed for five weeks.

```bash
systemctl list-timers ifiplatform-backup.timer     # "LAST" should be this morning, "NEXT" tomorrow 05:00
journalctl -u ifiplatform-backup -n 20             # last runs; look for "Backup completed"
ls -lt /mnt/backups/postgres/ | head -3            # newest dumps, with dates
ls -lt /mnt/backups/media/ | head -3               # newest media archives
df -h /mnt/backups                                 # space left on the backup volume
```

If the newest file is more than a day old, read the journal for the
error. Common causes:

| Error                               | Cause                                                          |
| ----------------------------------- | -------------------------------------------------------------- |
| `/mnt/backups is not mounted`       | The volume is detached. Check it in the NREC dashboard, then `sudo mount -a` |
| `Permission denied`                 | A folder under `/mnt/backups` isn't owned by `ubuntu`. Fix with `sudo chown -R ubuntu:ubuntu /mnt/backups/<folder>` |
| `password authentication failed`    | The `DB_*` values in `.env` don't match the database            |
| `No space left on device`           | The volume is full. Check `df -h /mnt/backups`                  |

Backups from before the timer was set up (September 29, 2026) were run by
cron and logged to `~/postgres_backup.log`.

## Taking a backup by hand

Do this before anything risky: a manual data fix, a tricky migration run
by hand, or a restore.

```bash
bash /home/ubuntu/IfiPlatform/deploy/backup/backup_db.sh
```

Or start the systemd job, so the run shows up in its journal:

```bash
sudo systemctl start ifiplatform-backup
journalctl -u ifiplatform-backup -n 5
```

## Testing a restore

A backup you have never restored is a guess. Restore into a scratch
database, look around, then delete it. This doesn't touch the live site.

```bash
ls -lt /mnt/backups/postgres/ | head -3     # pick a dump

sudo -u postgres createdb restore_test
sudo -u postgres pg_restore --no-owner -d restore_test < /mnt/backups/postgres/<file>.dump

# Compare a few counts with the live database (DB_NAME in .env)
sudo -u postgres psql restore_test -c "SELECT count(*) FROM wagtailcore_page;"
sudo -u postgres psql <db_name>    -c "SELECT count(*) FROM wagtailcore_page;"
sudo -u postgres psql restore_test -c "SELECT count(*) FROM wagtailimages_image;"

sudo -u postgres dropdb restore_test        # clean up
```

For the media archive, unpack it somewhere harmless and look inside:

```bash
mkdir /tmp/media_test
tar -xzf /mnt/backups/media/media_<timestamp>.tar.gz -C /tmp/media_test
ls /tmp/media_test/media/
rm -r /tmp/media_test
```

The `<` feeds the file in from your own shell, so the `postgres` user
doesn't need permission to read `/mnt/backups`. `restore_test` lives on
the VM's own disk. The database is small, but
check `df -h /` first.

## Restoring production

Use this when the live database or `media/` is broken, for example after
a bad migration or a mistaken bulk delete. Anything saved after the backup
was taken is lost, so pick the newest backup from before the problem.

Don't do this around 01:00, when the nightly deploy runs.

```bash
cd /home/ubuntu/IfiPlatform

# 1. Back up the current state, even if it's broken. It's your way back
#    if the restore goes wrong.
bash deploy/backup/backup_db.sh

# 2. Pick a dump and the media archive with the SAME timestamp.
ls -lt /mnt/backups/postgres/ /mnt/backups/media/

# 3. Stop the site.
sudo systemctl stop gunicorn

# 4. Replace the database. <db_name> and <db_user> are DB_NAME and DB_USER in .env.
sudo -u postgres dropdb <db_name>
sudo -u postgres createdb -O <db_user> <db_name>
sudo -u postgres pg_restore --no-owner --role=<db_user> -d <db_name> < /mnt/backups/postgres/<db_name>_<timestamp>.dump

# 5. Replace media/. The old folder is kept until you're sure.
mv ifiplatform/media ifiplatform/media.before-restore
tar -xzf /mnt/backups/media/media_<timestamp>.tar.gz -C ifiplatform/

# 6. Start the site again and clear the cache.
sudo systemctl start gunicorn
cd ifiplatform && ../venv/bin/python manage.py clear_cache
```

Then check the site in a browser: a few pages, some images, and the
Wagtail admin. When everything looks right, delete
`ifiplatform/media.before-restore`.

If the backup is from before a migration that is now in the code, run
`python manage.py migrate` before starting Gunicorn.

### Old `.sql.gz` backups

Backups made before the switch to `.dump` files were saved as `.sql.gz`.
Check which kind of file you have:

```bash
gunzip -c <file>.sql.gz | head -c 5
```

- `PGDMP` means custom format: `gunzip -c <file>.sql.gz | sudo -u postgres pg_restore --no-owner -d <target_db>`
- Readable SQL (`--` or `SET`) means plain format: `gunzip -c <file>.sql.gz | sudo -u postgres psql <target_db>`

## Copying backups outside NREC

Not automated yet. Every so often (for example monthly, and before big
changes to the server), copy the newest pair to your own machine:

```bash
# Run on your own computer, not the server
scp <user>@<server>:/mnt/backups/postgres/<db_name>_<timestamp>.dump .
scp <user>@<server>:/mnt/backups/media/media_<timestamp>.tar.gz .
```

The database holds personal data (user accounts and email addresses).
Store the copies **encrypted**, in storage only maintainers can reach,
such as UiO's storage services. Never in a public or shared folder. Delete
old copies you no longer need.

## The analytics VM

Umami (the traffic statistics) runs on its own VM with its own backup:
`/usr/local/bin/backup_umami.sh`, run by cron at 05:00, writing to
`/mnt/backups/umami/` on that VM, kept for 14 days, logged to
`~/umami_backup.log`. It works the same way as the platform backup, but
only covers the database, since Umami keeps no files. It is not part of
this repo.

## Still to do

- **Test a restore** into `restore_test` and write the date here. Not done
  yet for either VM.
- **Automate copies outside NREC.**
- **Alert when a backup fails.** Today a failed nightly run only shows up
  in the journal. A failed backup during a deploy does show up, as a
  failed GitHub Actions run.
