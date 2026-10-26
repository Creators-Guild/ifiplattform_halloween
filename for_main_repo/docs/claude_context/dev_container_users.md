# Dev container users: dev and app

Last updated: 2026-10-26
Covers: Dockerfile.dev, docker-compose.yml, tools/ifi/restart-server, ifi

## Why two users

Everything used to run as `dev`, including the compose start command
(`migrate`, `createcachetable`, `seed_dev_data`,
`runserver`). That command runs code from whatever branch is checked out,
without the student doing anything. `dev` also owns the logins:
`/home/dev/.claude/.credentials.json` (Claude Code's OAuth token, in plain
text in the `claude-config` volume), and earlier the gh token (see
ifi_account.md). So the site now runs as a system user `app`
(compose `user: app`). Terminals still open as `dev` (`remoteUser: dev` in
.devcontainer/devcontainer.json, `-u dev` in the root `ifi` launcher).

What `app` can't reach (checked 2026-10-25): `/home/dev` (chmod 700 in
Dockerfile.dev). VS Code's sockets in /tmp (`vscode-remote-containers-ipc-*`,
which forwards git credential requests to the host,
`vscode-ssh-auth-*` the SSH agent, `vscode-ipc-*`, `vscode-wayland-*`,
`.X11-unix/X0`) are `srwxr-xr-x dev`. Connecting needs write permission, so
only `dev` can use them. If a VS Code update makes them world-writable, this
protection is gone for the host logins. Re-check with `ls -la /tmp`.

Not covered: code `dev` runs itself (`manage.py test`, `shell`, Claude Code's
own commands) can still read the tokens. This only protects against code that
starts by itself. The user decided (2026-10-26) to leave the `claude-config`
volume as it is. It lives on the dev's own computer, and a leak costs Claude
usage, not code. docker_guide.md ("Your Claude Code login") tells devs to
`/logout` on shared computers, which keeps chat history. No volume
encryption: Docker has none built in, FUSE-based encryption needs
`SYS_ADMIN`, and the volume has to be unlocked while Claude Code runs anyway.
Host disk encryption covers the lost-laptop case.

## What app needs, and how it gets it

- **Reads** the project through the bind mount. Fine with normal 644/755
  host permissions.
- **Uploads**: `MEDIA_ROOT=/srv/media`, the `media` named volume.
  Dockerfile.dev creates `/srv/media` owned by `app`, so the new volume
  copies that ownership. settings.py reads `MEDIA_ROOT` from the env (prod
  doesn't set it). The start command copies the old bind-mounted
  `ifiplatform/media` into the volume once, when the volume is empty. It uses
  `cp -r`, not `-a`, since `app` can't keep dev's ownership.
  `dev` writes there too: the test content (`seed_dev_data/helpers.py`,
  used by `seed_dev_data` in `ifi reset-database`) saves images. So
  `dev` is in `app`'s group, `/srv/media` is 2775 (setgid, so new folders
  get group `app`), and settings.py sets `FILE_UPLOAD_DIRECTORY_PERMISSIONS
  = 0o2775` / `FILE_UPLOAD_PERMISSIONS = 0o664` whenever `MEDIA_ROOT` comes
  from the env. The start command also runs `chmod -R g+w` plus
  `find -type d -exec chmod g+s`. That fixes folders made before this
  (`cp -r` and early uploads were 755). It's quiet, because `app` can't
  chmod `dev`'s files, and those are already group-writable anyway.
  Reported 2026-10-26: PermissionError on `/srv/media/original_images/...`
  from the reset before this.
- **Cache**: Django's FileBasedCache makes its dir 0700 and files 0600
  (mkstemp), so two users can't share it. The dev's own manage.py commands
  (`seed_dev_data`, wagtail signals) must invalidate the site's cache,
  e.g. site-root paths (see the CACHES comment in settings.py). So with
  `CACHE_IN_DATABASE=True` (set only in docker-compose.yml) it's
  DatabaseCache, table `django_cache`, created by `createcachetable` in the
  start command and in `ifi reset-database` (which drops the schema). The test
  runner still overrides to LocMem.
- **Restart**: `dev` can't signal `app`'s processes, so
  `ifi restart-server` runs `sudo -u app pkill ...`, and its fallback starts
  runserver with `sudo -u app`.
  `/etc/sudoers.d/dev-as-app`: `dev ALL=(app) NOPASSWD: ALL` and
  `Defaults>app !env_reset, always_set_home` (keeps the compose env such as
  DB_* and MEDIA_ROOT, but HOME=/home/app). That gives dev nothing new,
  since app has fewer rights than dev. There's no rule for app and none for
  root.
- `app` is `useradd --system`, so its UID is below 1000 and never clashes
  with the host UID that VS Code gives `dev` (updateRemoteUserUID).

## Prod

The prod Dockerfile already runs as `app`, with media/ and django_cache/
volumes. There every command runs as `app`, so the file cache is fine. Don't
copy CACHE_IN_DATABASE there.
