# Access and handover

Last updated: 2026-09-29

Every account and key the project depends on, who controls it, and what
to do when someone joins or leaves. If the only person with access to one
of these leaves without handing it over, that part of the project is lost.

**This repo is public.** Write roles and where to check, never passwords,
keys, tokens or personal contact details.

## Accounts and access

Fill in the blanks. "Owner" is the account that can add and remove other
people. "Who has access" is where to look up the current list, since a
list of names here would go out of date.

| System | Used for | Owner (role or org) | Who has access: where to check |
| ------ | -------- | ------------------- | ------------------------------ |
| NREC project | Both VMs, the backup volumes, security groups | _(fill in)_ | NREC dashboard → project members |
| SSH, platform VM | Logging in to the server, deploys | _(fill in)_ | `~/.ssh/authorized_keys` on the server |
| SSH, analytics VM | Umami server | _(fill in)_ | `~/.ssh/authorized_keys` on that server |
| GitHub `Creators-Guild` | Code, issues, Actions, secrets | _(fill in)_ | Org → People, repo → Settings → Collaborators |
| Domain `ifiplattform.no` | DNS for the site and `stats.` | _(fill in: registrar)_ | _(fill in)_ |
| Email (SMTP) | Account verification emails | _(fill in: provider)_ | _(fill in)_ |
| DeepL | Machine translation | _(fill in)_ | DeepL account → team members |
| Umami | Traffic statistics | _(fill in)_ | Umami → Settings → Users |
| Trello | Board that mirrors GitHub issues | _(fill in)_ | Trello board → members |
| Wagtail admin | Editing the site | Site superusers | Wagtail admin → Settings → Users |
| Let's Encrypt | HTTPS certificates, expiry warnings | _(fill in: email Certbot registered)_ | `sudo certbot show_account` on the server |
| Figma | Design files | _(fill in)_ | Figma → file/team sharing |
| _(add any missing)_ | | | |

**Where the shared secrets are kept:** _(fill in, for example a shared
password manager)_. The server's `.env` must never be the only copy: if
the VM is lost, so are the values (see
[backups_and_recovery.md](backups_and_recovery.md#what-is-not-covered)).

### GitHub secrets

Set in the repo under Settings → Secrets and variables → Actions.

| Secret | Used by | Comes from |
| ------ | ------- | ---------- |
| `SERVER_IP` | `deploy.yml` | The platform VM's IP in NREC |
| `SERVER_USER` | `deploy.yml` | `ubuntu` |
| `SSH_PRIVATE_KEY` | `deploy.yml` | The deploy key; its public half is in `authorized_keys` on the server |
| `TRELLO_KEY`, `TRELLO_TOKEN` | `trello_sync.yml` | The Trello account above |

The deploy key logs in as `ubuntu`, which has full sudo, so **this secret
gives root access to the server**. Keep the list of repo admins short.

## Adding a person

Only give what the role needs. An editor needs a Wagtail account, not SSH.

- [ ] **GitHub:** add to the `Creators-Guild` org or as a repo
      collaborator, with the lowest role that works.
- [ ] **SSH** (maintainers only): ask for their *public* key and add it on
      its own line:
      ```bash
      nano ~/.ssh/authorized_keys                # add one line: ssh-ed25519 AAAA... name
      ```
      Put their name or handle at the end of the line, so you know whose key
      it is when removing it later. Have them test logging in before you
      close your own session.
      Key pairs in the NREC dashboard are only copied in when a VM is
      *created*. Changing them there does nothing to a running VM, so SSH
      access is always managed in `authorized_keys`.
- [ ] **NREC** (maintainers only): add them to the project.
- [ ] **Wagtail admin:** create the account, or promote their existing one,
      in Settings → Users.
- [ ] **Other accounts** from the table, only as needed.
- [ ] **Shared secrets:** give access to where they're kept, never by chat
      or email.

## Removing a person

Do this the same week someone leaves, even on good terms.

- [ ] **GitHub:** remove them from the org or repo.
- [ ] **SSH:** delete their line from `~/.ssh/authorized_keys` on **both**
      VMs.
- [ ] **NREC:** remove them from the project.
- [ ] **Wagtail admin and Umami:** deactivate their accounts.
- [ ] **Other accounts** from the table: remove them.
- [ ] **If they owned an account** (domain, DeepL, email, Trello): transfer
      ownership *before* they leave (see [Handover](#handover)).
- [ ] **Replace shared secrets they knew.** They may have copies. At least:
  - [ ] the **deploy key** (see below), if they were a repo admin or had
        the key
  - [ ] `DJANGO_SECRET_KEY`, `DB_PASSWORD`, `DEEPL_API_KEY`,
        `EMAIL_HOST_PASSWORD` in `.env`, if they had server access.
        After changing `.env`, run `sudo systemctl restart gunicorn`.
        A new `DB_PASSWORD` also has to be set in PostgreSQL:
        `sudo -u postgres psql -c "ALTER USER ifiplatform_user PASSWORD '<new>';"`
  - [ ] the Trello token, if it was theirs

Changing `DJANGO_SECRET_KEY` logs everyone out and invalidates any
password reset links that are still open, which is harmless.

### Replacing the deploy key

On your own computer:

```bash
ssh-keygen -t ed25519 -f ifiplatform_deploy -C "github-actions-deploy"   # no passphrase
```

1. On the server, add the contents of `ifiplatform_deploy.pub` as a new
   line in `~/.ssh/authorized_keys`.
2. In GitHub, set the `SSH_PRIVATE_KEY` secret to the contents of
   `ifiplatform_deploy` (the file without `.pub`).
3. Run the deploy workflow by hand to check that it works.
4. Delete the old deploy key's line from `authorized_keys`.
5. Delete both key files from your computer.

## Handover

When the current maintainers are about to leave the project:

- [ ] Every account in the table has at least **two** people with owner
      access, and at least one of them is staying.
- [ ] Ownership of the domain, NREC project and GitHub org is transferred
      to someone who is staying, or to an organisation (such as the
      student group or UiO) rather than a personal account.
- [ ] The new maintainers have logged in to the server, run a deploy and
      read [prod_server.md](prod_server.md),
      [backups_and_recovery.md](backups_and_recovery.md) and
      [server_setup.md](server_setup.md).
- [ ] Payment details on any paid account (domain, DeepL, email) are
      moved, so nothing expires unnoticed.
- [ ] The table above is up to date, and the date at the top is changed.
