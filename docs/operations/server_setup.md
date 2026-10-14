# Server setup

Last updated: 2026-10-14

How to build the production server from zero, for example if the VM is
lost or has to be replaced. Follow the steps in order. For how the
finished server works, see [prod_server.md](prod_server.md). For restoring
data, see [backups_and_recovery.md](backups_and_recovery.md).

The config files used below are copies in
[deploy/server_config/](../../deploy/server_config/). Nothing installs
them automatically, so each step copies them by hand.

Placeholders: `<server-ip>` is the new VM's IP address, `<db_password>`
is a new password you choose. Never write real values into this repo.

## What you end up with

| Part       | Version / setting                                              |
| ---------- | -------------------------------------------------------------- |
| OS         | Ubuntu 24.04 LTS on NREC, `m1.medium` (1 vCPU, 4 GB RAM, 20 GB disk) |
| Python     | 3.12 (Ubuntu's own)                                            |
| PostgreSQL | 16 (Ubuntu's own)                                              |
| Web        | Nginx → Gunicorn over a Unix socket → Django                   |
| Backups    | Separate 20 GiB volume at `/mnt/backups`                        |

## 1. Create the VM in NREC

In the NREC dashboard:

1. **Instance:** Ubuntu 24.04 image, flavor `m1.medium`, network
   `dualStack` (public IPv4 and IPv6), and your SSH key pair.
2. **Security group:** allow only ports 22 (SSH), 80 (HTTP) and 443
   (HTTPS).
3. **Backup volume:** attach the existing `ifiplattform-backups` volume if
   it survived. It holds the backups you'll restore from in step 7.
   Otherwise create a new 20 GiB volume (type `mass-storage-default`) and
   attach it.

Then log in:

```bash
ssh ubuntu@<server-ip>
```

## 2. Install packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-venv postgresql nginx certbot python3-certbot-nginx fail2ban
```

If the upgrade says "Pending kernel upgrade", run `sudo reboot`, wait a
minute and log in again.

**Move the automatic upgrades to 04:00.** They can briefly restart
PostgreSQL and Nginx, so they should run at night and finish before the
05:00 backup:

```bash
sudo systemctl edit apt-daily-upgrade.timer
```

Add this in the editor, then save:

```ini
[Timer]
OnCalendar=
OnCalendar=*-*-* 04:00
RandomizedDelaySec=30m
```

The empty `OnCalendar=` line is needed. It clears Ubuntu's default time
before setting the new one.

## 3. Mount the backup volume

Find the volume's device name. It's the disk of the right size with no
mount point, often `/dev/sdb`:

```bash
lsblk
```

**Only if the volume is new and empty**, format it. This erases
everything on it, so never run it on the old backup volume:

```bash
sudo mkfs.ext4 /dev/sdb
```

Then attach it at `/mnt/backups`, now and on every boot:

```bash
sudo blkid /dev/sdb                          # copy the UUID="..." value
sudo mkdir -p /mnt/backups
sudo nano /etc/fstab                         # add the line below
```

```
UUID=<volume-uuid>  /mnt/backups  ext4  defaults,nofail  0  2
```

`nofail` lets the VM boot even if the volume is missing.

```bash
sudo mount -a                                # mount everything in fstab
df -h /mnt/backups                           # should show the volume's size
sudo chown ubuntu:ubuntu /mnt/backups
sudo chmod 700 /mnt/backups                  # backups contain personal data
mkdir -p /mnt/backups/postgres /mnt/backups/media
```

The last command runs **without** `sudo`, so the folders belong to
`ubuntu`, the user the backup runs as. Folders owned by `root` make every
backup fail with "Permission denied".

## 4. Create the database

The names match `.env.example`. Choose a new password and keep it for
step 5.

```bash
sudo -u postgres createuser --pwprompt ifiplatform_user
sudo -u postgres createdb -O ifiplatform_user ifiplatform
```

## 5. Install the app

```bash
cd /home/ubuntu
git clone https://github.com/Creators-Guild/IfiPlatform.git
cd IfiPlatform
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/pip install gunicorn                # not in requirements.txt, see below
```

**Create `.env`:**

```bash
cp ifiplatform/.env.example ifiplatform/.env
chmod 600 ifiplatform/.env                   # only ubuntu can read the secrets
nano ifiplatform/.env
```

Fill in every key listed in
[prod_server.md](prod_server.md#environment-variables). In particular:

- `DEBUG=False`
- `DJANGO_SECRET_KEY`: a new one from
  `venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DB_PASSWORD`: the password from step 4
- `DJANGO_ALLOWED_HOSTS=ifiplattform.no,www.ifiplattform.no`
- `CSRF_TRUSTED_ORIGINS=https://ifiplattform.no,https://www.ifiplattform.no`
- `EMAIL_*`, `DEEPL_API_KEY`: from the email provider and DeepL accounts
- `UMAMI_SCRIPT_URL`, `UMAMI_WEBSITE_ID`: from the Umami dashboard
- `DEEPL_GLOSSARY_ID`: leave empty. Step 11 fills it in.

## 6. Let Nginx reach the static and media files

Nginx runs as the user `www-data`. To serve files from inside
`/home/ubuntu`, it must be allowed to pass through that folder:

```bash
chmod 751 /home/ubuntu
```

The final `1` lets other users pass through the folder without being able
to list what's in it. Without it, CSS and images give "403 Forbidden".

## 7. Restore the data, or start empty

**Restoring (the usual case):** use a database dump and media archive
with the same timestamp (see
[backups_and_recovery.md](backups_and_recovery.md#summary)). If the old
backup volume is gone, use the newest copy stored outside NREC.

```bash
cd /home/ubuntu/IfiPlatform
ls -lt /mnt/backups/postgres/ /mnt/backups/media/      # pick a matching pair
sudo -u postgres pg_restore --no-owner --role=ifiplatform_user -d ifiplatform < /mnt/backups/postgres/ifiplatform_<timestamp>.dump
tar -xzf /mnt/backups/media/media_<timestamp>.tar.gz -C ifiplatform/
```

This is a shorter version of
[Restoring production](backups_and_recovery.md#restoring-production). On
a new server there is no live site to stop and no old data to move out of
the way first.

**Starting empty (a brand-new site only):**

```bash
cd /home/ubuntu/IfiPlatform/ifiplatform
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser
```

Either way, then collect the static files:

```bash
cd /home/ubuntu/IfiPlatform/ifiplatform
../venv/bin/python manage.py migrate         # no-op if the backup is up to date
../venv/bin/python manage.py collectstatic --noinput
```

## 8. Start Gunicorn

```bash
cd /home/ubuntu/IfiPlatform
sudo cp deploy/server_config/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
systemctl status gunicorn                    # should say "active (running)"
```

Gunicorn listens on a Unix socket, `ifiplatform/ifiplatform.sock`, not a
port. `Group=www-data` in the unit file lets Nginx connect to that socket.

## 9. Point the domain at the new server

At the domain registrar, change the DNS records for `ifiplattform.no` and
`www.ifiplattform.no` to the new IP addresses: an `A` record for IPv4 and
an `AAAA` record for IPv6. Certbot in the next step only works once these
point at the new server. Check with:

```bash
dig +short ifiplattform.no www.ifiplattform.no
```

## 10. Set up Nginx and HTTPS

The copy in `deploy/server_config/nginx/ifiplatform` already contains the
HTTPS lines Certbot added, but on a new server the certificates don't
exist yet, so Nginx would refuse that file. Start with this HTTP-only
version instead, and let Certbot add the rest:

```bash
sudo nano /etc/nginx/sites-available/ifiplatform
```

```nginx
server {
    listen 80;
    server_name www.ifiplattform.no;

    location /static/ {
        alias /home/ubuntu/IfiPlatform/ifiplatform/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/IfiPlatform/ifiplatform/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/IfiPlatform/ifiplatform/ifiplatform.sock;
    }
}

server {
    listen 80;
    server_name ifiplattform.no;
    return 301 https://www.ifiplattform.no$request_uri;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ifiplatform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default     # Ubuntu's "Welcome to nginx" page
sudo nginx -t                                # test the config
sudo systemctl reload nginx

sudo certbot --nginx -d ifiplattform.no -d www.ifiplattform.no
sudo certbot renew --dry-run                 # check that renewal will work
```

List `ifiplattform.no` first: the certificate is named after the first
domain, and the config expects `/etc/letsencrypt/live/ifiplattform.no/`.

Afterwards, compare the result with the copy in `deploy/server_config/`:

```bash
diff /etc/nginx/sites-available/ifiplatform deploy/server_config/nginx/ifiplatform
```

The only difference should be the IP address. The old server also listed
its IP in `server_name`, which isn't needed.

## 11. fail2ban, SSH and the first deploy

**fail2ban:**

```bash
sudo cp deploy/server_config/fail2ban/jail.local /etc/fail2ban/jail.local
sudo systemctl restart fail2ban
sudo fail2ban-client status                  # sshd, nginx-http-auth, nginx-botsearch
```

**SSH:** check that password logins are off. Ubuntu's cloud image does
this by default:

```bash
sudo sshd -T | grep -E 'passwordauthentication|permitrootlogin'
# should show: passwordauthentication no, permitrootlogin without-password
```

**GitHub:** in the repo's Settings → Secrets and variables → Actions,
update `SERVER_IP` to the new address. If the deploy key changed, update
`SSH_PRIVATE_KEY` and add its public key to `~/.ssh/authorized_keys` on
the server. `SERVER_USER` stays `ubuntu`.

**First deploy**, by hand. This installs the Peoply sync and backup timers,
and also takes the first backup:

```bash
cd /home/ubuntu/IfiPlatform
SKIP_COUNTDOWN=true bash deploy/deploy.sh
cd ifiplatform && ../venv/bin/python manage.py sync_deepl_glossary --write-env
sudo systemctl restart gunicorn              # load the new DEEPL_GLOSSARY_ID
```

## 12. Check everything

Run the routine checks from
[prod_server.md](prod_server.md#routine-checks), then:

- Open https://www.ifiplattform.no. Check a few pages, some images, and
  log in to the Wagtail admin.
- `systemctl list-timers`: `sync-peoply-events` and `ifiplatform-backup`
  are scheduled.
- `ls -lt /mnt/backups/postgres/ | head -3`: the first deploy wrote a
  backup.
- Run a deploy from GitHub Actions to check that the secrets work.

Then shut down or delete the old VM if it still exists, and write the date
of the rebuild in this doc.

## Notes and known issues

- **Gunicorn isn't in `requirements.txt`.** It was installed into the venv
  by hand, which is why step 5 installs it separately. Adding it to
  `requirements.txt`, pinned to the version on the server
  (`venv/bin/pip show gunicorn`), would remove that extra step.
- **Uploads over 1 MB probably fail.** The Nginx config has no
  `client_max_body_size`, so Nginx's 1 MB default applies. Uploading a
  larger image or document in the Wagtail admin then fails with
  "413 Request Entity Too Large". Adding `client_max_body_size 20M;` to
  the `www.ifiplattform.no` server block fixes it.
- **Gunicorn's timeout is 30 minutes** (`--timeout 1800`). The usual value
  is 30–120 seconds. A long timeout means a stuck request holds one of
  the three workers for up to half an hour.
- **sudo is intentionally broad.** `ubuntu` has passwordless sudo for
  everything (see [prod_server.md](prod_server.md#security)). Commands
  still need `sudo` in front, so nothing changes system files by accident,
  and the automatic deploy needs sudo without a password. The trade-off:
  the deploy SSH key gives full root access, so keep the GitHub secrets
  and the list of repo admins small, and replace the key when a maintainer
  leaves.
- **Docker** replaces most of these steps on the servers that use it. The
  setup is ready and runs the Halloween mock site, see
  [docker_server.md](docker_server.md). The real site keeps this setup
  until it moves over, which also means rewriting the backups and the
  scheduled jobs for Docker.
