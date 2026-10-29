# Plan: research numbers from the Halloween mock site

Last updated: 2026-10-29

The mock site (halloween.ifiplattform.no) must be deleted on
**2 November 2026**, as its privacy policy promises. Before that, Hanna
takes a few **anonymous totals** from it for her master's thesis. The
Sikt application (change notice of 2026-10-29) and the information letter
for the event's participants promise exactly this, and nothing more:

> From the mock site, only anonymous, aggregated numbers are taken
> before the site is deleted on 2 November 2026; no data about
> individuals.

Totals are not personal data, so this may be done before Sikt has
approved the change notice. Delete this plan when the site is deleted.

## What to count

Exactly these four numbers (from the Sikt variable list for the event),
plus the issue counts under "Extra" below, nothing else:

1. Registered accounts in total.
2. Accounts that connected a GitHub account.
3. Accounts that solved at least one task.
4. Accounts that were created without doing anything more (no GitHub
   connection and no task attempted).

**Check in the code first** and write the answers into this plan:

- Which model and field means "connected GitHub"?
- What counts as "solved a task" (a completed task row, a merged PR, a
  score)? Use what the site itself showed as solved.
- What counts as "doing something" for number 4?
- Which accounts to leave out. These org and helper accounts are not
  participants and must not be counted in any of the four numbers:
  `admin`, `andreval`, `halloween-admin`, `arin`, `attilaac`,
  `geiteadmin`, `stefanna`, `whistler`, `test`. Match the whole username,
  ignoring case, never a prefix, so a participant called `tester` is
  still counted. If any other account is a superuser or staff, stop and
  ask Hanna before leaving it out. Count how many were left out (only the
  number).

### Extra: how credit was decided (issue counts only)

Not on the Sikt variable list. These are counts of issues, not people.
They record how far the site's leaderboard differed from what GitHub
alone shows, which can't be found out after the site is deleted. Claims
and credit overrides only ever lived in the site's database: the site
read from GitHub but never wrote to it. The rules are in
`commits_app/github_sync.py` (`_credit`), checked in this order:

5. Issues that gave points in total (`Credit` rows).
6. Credited by an organiser's `CreditOverride`.
7. Credited to whoever claimed the issue on the site (`Claim`).
8. Of number 7: issues with no merged PR (`Credit.pr_number` empty), so
   nothing on GitHub links the issue to the person who got it.
9. Credited from GitHub alone (merged PR author or first assignee).

6 + 7 + 9 = 5. Leave out credits that went to an excluded account's
linked GitHub username. Never output issue numbers, usernames or any
row per issue: issue numbers and public GitHub data together could
point to a person.

## How

1. Add a small read-only management command in the mock site repo, for
   example `halloween_totals`, that prints the totals as CSV (see
   "The CSV" below) to stdout. It must never print or log names,
   usernames, emails, GitHub IDs or anything per account. A short test
   with made-up accounts checks the four numbers and the CSV columns.
2. Deploy it, then on the mock server run:
   `docker compose exec -T web python manage.py halloween_totals > halloween_totals.csv`
   (`-T` keeps terminal control characters out of the file).
3. Open the CSV, check it, and fill in by hand the rows the command
   can't know: the commit hash of the code that counted them and the
   Peoply sign-up number.
4. Keep that file in Hanna's research folder on UiO OneDrive, with the
   rest of the analysis data, and delete the copy on the server. It's not
   personal data, so it could live anywhere, but don't commit the exact
   numbers to a public repo: the thesis reports 1–4 as "fewer than 5".

Also note, while it's still visible: the number of people signed up on
Peoply (a single number, same file).

## The CSV

One file, `halloween_totals.csv`, UTF-8, comma-separated, a header row,
one row per measure. Only totals: never one row per account, since the
promise to Sikt and the participants is "no data about individuals".

```
measure,value,definition
accounts_total,<n>,<rule from "Check in the code first">
accounts_github_connected,<n>,<model and field>
accounts_solved_task,<n>,<what counts as solved>
accounts_did_nothing,<n>,<what counts as doing something>
accounts_excluded,<n>,"org/helper accounts on the list above"
issues_credited,<n>,"issues that gave points, excluded accounts left out"
issues_credited_by_override,<n>,"organiser CreditOverride"
issues_credited_by_claim,<n>,"claimed on the site"
issues_credited_by_claim_without_pr,<n>,"claimed, no merged PR"
issues_credited_by_github,<n>,"merged PR author or first assignee"
peoply_signups,<n>,"Peoply event page, read by hand"
taken_at,<Oslo time with offset, e.g. 2026-10-30T14:05+01:00>,
commit,<hash>,"mock site repo, code that counted"
```

## Don't

- Don't copy the database, a dump, a backup or any per-account rows off
  the server, not even "just in case". The promise is totals only.
- Don't move any of the mock site's data to IfiPlatform. Only the small
  file of totals is kept.
- Don't fetch per-person GitHub data from the event repo now. That needs
  the participant's consent (UiO Nettskjema) and Sikt's approval first,
  and it happens later on IfiPlatform's server (see "Later").

## Then delete the site (on 2 November 2026)

The privacy notice
(`ifiplatform/apps/account_app/templates/legal/event_privacy_notice.html`)
promises: "The whole mock site, including every account, is deleted no
later than 2 November 2026." Server logs with IP addresses are also
covered, since they are part of the site.

The wipe on the VM runs by itself from a one-shot systemd timer. The NREC
resources and DNS are deleted by hand the same day, because doing that
automatically would mean leaving an OpenStack credential with delete
rights on the VM.

**The wipe runs whether or not the totals were taken.** The promise to
participants comes first. Take the CSV by 1 November.

### Automatic wipe on the VM

Add to the repo:

- `deploy/halloween/wipe_mock_site.sh`. It runs as root, keeps going if
  one step fails, and exits non-zero at the end if any step failed. In
  order, it:
  1. Stops and disables every timer that could bring data back or make a
     new copy: `ifiplatform-backup`, `sync-peoply-events`, and the
     translate timers, whichever exist on the server.
  2. Runs `docker compose -f compose.prod.yml down -v --remove-orphans`
     in the site folder. That removes the containers (and their Docker
     logs, which hold the IP addresses) and the volumes `pgdata`, `media`,
     `cache`, `caddy_data` and `caddy_config`.
  3. Deletes everything under `/mnt/backups/postgres/` and
     `/mnt/backups/media/`, if they exist. Check first which backup setup
     the mock server really uses: `backup_db.sh` has the old non-Docker
     paths (`/home/ubuntu/IfiPlatform`).
  4. Deletes `.env`, both in the repo root and in `ifiplatform/.env`.
  5. Logs only what it removed (for example "deleted 14 backup files"),
     never any content. View the log with `journalctl -u halloween-wipe`.
  6. Writes `/var/lib/halloween-wipe/done` with the time, so a second run
     does nothing.

  With `--dry-run` it only lists what it would delete.
- `deploy/halloween/halloween-wipe.service` (oneshot, runs the script)
  and `halloween-wipe.timer` with
  `OnCalendar=2026-11-02 09:00:00 Europe/Oslo` and `Persistent=true`, so
  it still runs at the next boot if the VM was off at 09:00. It runs at
  09:00, not at midnight, so someone is awake to see that it worked.

Test before installing: run the script with `--dry-run` on the server,
and for real against a throwaway Compose project in the dev container
with dummy volumes and a fake `/mnt/backups`. After installing, check
that `systemctl list-timers halloween-wipe.timer` shows 2 November 09:00.

Before the wipe, **turn off the deploy workflow** for the mock server
(GitHub → Actions → the deploy workflow → Disable workflow). Otherwise a
push to `main` brings the site back up with an empty database, and
`deploy.sh` makes a new backup first.

### Checklist

- [ ] By 1 Nov: the four totals are saved in the CSV and checked.
- [ ] By 1 Nov: wipe script and timer tested, installed and showing the
      right time. Deploy workflow disabled.
- [ ] 2 Nov, after 09:00: `journalctl -u halloween-wipe` shows that every
      step succeeded, `docker volume ls` shows no site volumes, and
      `/mnt/backups` is empty. If something failed, finish it by hand
      the same day.
- [ ] 2 Nov, by hand: check for any backup copies made outside NREC
      (see "Copying backups outside NREC" in
      `docs/operations/backups_and_recovery.md`) and delete them.
- [ ] 2 Nov, by hand in NREC: delete the VM, its disks, the
      `ifiplattform-backups` volume (if it belongs to the mock site) and
      any snapshots. Only this really removes the data from the disks.
- [ ] 2 Nov, by hand: remove the `halloween` DNS record.
- [ ] 2 Nov, by hand: remove the mock site's `.env` and secrets wherever
      else they're stored (password manager, GitHub Actions secrets for
      the deploy).
- [ ] Write down the date it was deleted (the letter says it was deleted
      on 2 November 2026).

**Keep the event's GitHub repository.** It is not part of the mock site,
and the research needs it later. Archiving it (read-only) is fine;
deleting it is not, at least until the analysis is done (by 30.06.2027).

## Later (after Sikt approves, not part of this plan)

For participants who consent in Nettskjema: fetch their activity in the
event repo (forks, pull requests, tasks solved and difficulty, forked
without solving) to **IfiPlatform's server on NREC**, give each a random
research ID, store the link (ID ↔ GitHub username or email) encrypted
and apart from the analysis data, and delete the link and the Nettskjema
answers by 30.06.2027. How exactly is decided in the IfiPlatform repo
(`docs/research/data_handling.md`, question 14).
