# Custom manage.py commands

Last updated: 2026-10-13

This project's own `manage.py` commands, beyond Django's built-in ones
(`migrate`, `createsuperuser`, `test`, `makemessages`/`compilemessages`,
etc. — see [contributing/everyday_commands.md](../contributing/everyday_commands.md) for those), documented here
in one place, sectioned by the app each command lives in.

## ifi_home_app

### seed_dev_data

```bash
python manage.py seed_dev_data [--force]
```

Fills a fresh local database with a dummy article tree (index pages,
categories, a test article, a test student union, a test tool, and a
sample event) so you're not starting from a blank site. Covered in the
main setup flow: Docker runs it on every start, and without Docker it's step 6 of
[contributing/setup_without_docker.md](../contributing/setup_without_docker.md).

It also creates an `admin` / `admin` superuser, so you can reach
django-admin and wagtail-admin without running `createsuperuser` by hand.
That part is skipped whenever `DEBUG` is off — including under `--force`,
unlike the rest of the seed data. Never use it anywhere reachable.

Refuses to run when `DEBUG` is off, as a guard against accidentally
seeding dummy data into what looks like a real (non-local) database.
`--force` overrides that check — mainly useful in tests, since Django's
test runner always forces `DEBUG=False` regardless of `.env`.

### translate_english

```bash
python manage.py translate_english [--nightly]
```

Fills in missing English with DeepL. Publishing a page or saving a menu
group, header message or other translated snippet puts it on a "waiting
for English" list (the `WaitingForEnglish` table). This command
translates everything on that list, one object at a time, and takes each
one off the list when it's done. Only text that is new or changed since
the last run goes to DeepL. English that a person has fixed is never
overwritten.

A failed object (DeepL quota, network trouble, a bad answer) stays on the
list with the error. It's tried again after 2, 4, 8 … up to 60 minutes.
The English editor in the Wagtail admin shows what's missing.

`--nightly` first puts everything that still has missing English on the
list, translates it, then deletes translation rows nobody needs any more
(for deleted pages, removed blocks, and old DeepL text for Norwegian that
has since changed).

Without `DEEPL_API_KEY` (local dev, tests) nothing goes to DeepL. On
production, two systemd timers run it. `deploy/deploy.sh` installs both
(see [`sync_peoply_events`](#automatic-scheduling) for how):

| Timer | Runs | Command |
|---|---|---|
| `ifiplatform-translate.timer` | every minute | `translate_english` |
| `ifiplatform-translate-nightly.timer` | 03:30 | `translate_english --nightly` |

So English shows up about a minute after publishing. If the timers stop,
pages still show; they just show Norwegian text with a "not translated
yet" notice until the timers run again. To check on them:

```bash
systemctl list-timers 'ifiplatform-translate*'
journalctl -u ifiplatform-translate.service -n 50
journalctl -u ifiplatform-translate-nightly.service
```

Superusers can switch automatic translation off under Settings →
Translation settings in the Wagtail admin. The "Machine-translate now"
button in the English editor still works then.

### update_translation_snapshot

```bash
python manage.py update_translation_snapshot
```

Rewrites `ifi_home_app/translation/translated_fields.json`, the list of
every place on every model that has English (for example `ArticlePage:
body → image → caption`). A test compares that list with the models, so
renaming or removing a translated field fails the tests instead of
silently losing its English. The test's message says what to do. Run this
command only when you have added or removed a translated field on
purpose.

### sync_deepl_glossary

```bash
python manage.py sync_deepl_glossary [--write-env]
```

Pushes `ifi_home_app/translation/glossary_terms.py`'s nb → en term list to
DeepL as a glossary, so DeepL honours those exact translations (or "don't
translate this," for proper nouns like tool/union names) on every
machine-translation call this project makes. DeepL glossaries can't be
edited in place, so this deletes any existing glossary with the same name
and recreates it — safe to re-run whenever `glossary_terms.py` changes.

Requires `DEEPL_API_KEY` set in `.env`. After running it, copy the
printed `glossary_id` into `DEEPL_GLOSSARY_ID` in `.env` and restart the
server. `--write-env` makes that `.env` change for you. `deploy/deploy.sh`
runs it with `--write-env` whenever `glossary_terms.py` changed.

The nightly `translate_english` run redoes DeepL English that contains a
glossary term and is older than the new glossary. English fixed by a
person is left alone.

**Careful:** local dev and production use the same DeepL account, and the
glossary is replaced by name. Running this anywhere invalidates the
`DEEPL_GLOSSARY_ID` everywhere else, and DeepL then fails with a 404 until
that `.env` gets the new ID.

### link_peoply_organizations

```bash
python manage.py link_peoply_organizations [--apply]
```

One-off/occasional helper for setting `peoply_organization_id` across
*every* real `UnionPage` at once, rather than one at a time in
wagtail-admin. For each live nb union missing the field, queries Peoply's
own name search and only accepts an **exact** case-insensitive match
against the org's display name or its `urlId` (Peoply's own shorthand,
e.g. `cyb` for "Cybernetisk Selskab") — confirmed the hard way that
Peoply's search is substring-based, not exact (querying `FU` returns
`FUI`, a real but unrelated union), so a naive first-result match risks
silently linking a union to someone else's events. Anything without an
exact match is reported, not guessed at — look those up by hand on
peoply.app.

**Dry run by default** — unlike most of this project's commands, this one
flips that default deliberately, since a wrong automated match has real
consequences (a union's page would start showing another union's events).
Pass `--apply` to actually write the matches.

Not something a fresh local dev database needs — `seed_dev_data`
deliberately only sets `peoply_organization_id` on 2 example unions
(`FADDERUKE_UNION_PEOPLY_IDS` in `seed_dev_data/constants.py`), so a
tester running `sync_peoply_events` locally only ever hits Peoply's real
API for a couple of unions, not dozens. This command is for getting a
*real* environment (production) fully covered, once.

### sync_peoply_events

```bash
python manage.py sync_peoply_events [--after YYYY-MM-DD]
```

Creates `EventPage`s from [Peoply](https://peoply.app) (the event platform
IFI's student unions actually use), one per `UnionPage` that has a
`peoply_organization_id` set (found in the union's own Peoply page URL —
edit the union in wagtail-admin to set it, or run `link_peoply_organizations`
above to set it for every union at once).

`--after` limits the sync to events starting on/after that date; defaults
to today, so a plain run only ever picks up upcoming events.

**Peoply is the source of truth for some fields.** An event already
synced (matched by `external_source="peoply"` + `external_uid`, Peoply's
own event ID) gets its title, dates, times, location, intro, Peoply URL and
sign-up URL (`PEOPLY_SYNCED_FIELDS` in `event_models.py`) overwritten on
every run if they changed on Peoply. Those fields are read-only in the
Wagtail admin for synced events, so no editor's change is silently
undone. Everything else (event type, colors, tags, map links, related
unions) is only set when the event is created, and belongs to editors
after that. An unchanged event gets no new revision.

**Removed events are unpublished, not deleted.** An event that was synced
before but no longer comes back from Peoply is unpublished and logged as a
`PeoplyRemovedEvent`, for a superuser to delete or archive in the Django
admin. If it reappears on Peoply, it's published again and the log row is
marked resolved.

New events are created in Norwegian and published immediately. DeepL
fills in their English about a minute later (see
[`translate_english`](#translate_english)).
`event_type` is inferred from the title — defaults to `"social"`, upgrades
to `"company"` when the title contains "Bedriftspresentasjon"; anything
else (deadline, academic) needs manual correction, since Peoply doesn't
expose a comparable category itself.

After syncing, the command clears Wagtail's site-root-paths cache itself,
so every caller (the scheduled timer, a local dev running it by hand, the
"Sync Peoply now" admin button) gets it for free. Bulk page creation and
deletion like this doesn't trigger Wagtail's own site-root-paths cache
invalidation (that only listens for `Site` row changes, not ordinary page
churn). Without the clear, links across the whole site can start
resolving to `href="None"` until the cache expires or gets cleared some
other way. This happened once; see [`clear_cache`](#clear_cache) below
for the full story.

#### Automatic scheduling

A systemd timer runs this automatically on the production server — every 6
hours (00:00/06:00/12:00/18:00), plus extra runs at 14:00 and 16:00 on
weekdays.
Unlike [`cleanup_unverified_accounts`](#cleanup_unverified_accounts), this
one doesn't need to be invoked from an external scheduler by hand — the
unit files live in [deploy/systemd/](../../deploy/systemd/) and are checked
into the repo.

No manual server-side setup needed — `deploy/deploy.sh`
copies `deploy/systemd/*` into `/etc/systemd/system/` and runs
`daemon-reload` + `enable --now` on every deploy. This runs unconditionally
on every deploy rather than needing its own separate first-time step
(idempotent, a no-op once nothing's changed), and any future change to
these unit files takes effect on the next deploy automatically. To do the
same thing by hand (e.g. testing a unit-file change before it's merged):
```bash
sudo cp deploy/systemd/sync-peoply-events.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sync-peoply-events.timer
```

The 14:00 and 16:00 weekday runs are meant as Norway-local time — `OnCalendar=` uses
the server's own system timezone, so check `timedatectl` on the server; if
it reports `UTC`, either `sudo timedatectl set-timezone Europe/Oslo` or add
an explicit ` Europe/Oslo` suffix to both `OnCalendar=` lines in
`sync-peoply-events.timer`.

To check on it:
```bash
systemctl status sync-peoply-events.timer   # is it enabled, when's the next run
systemctl list-timers sync-peoply-events.timer
journalctl -u sync-peoply-events.service    # output from past runs
```
To trigger a run immediately, independent of the schedule:
```bash
sudo systemctl start sync-peoply-events.service
```

### check_peoply_union_matches

```bash
python manage.py check_peoply_union_matches [--create-missing] [--parent-slug SLUG]
```

Cross-checks every live, `status="active"` nb `UnionPage` against Peoply's
*entire* organization roster (`GET /organizations`, paginated the same
skip/take way as `get_events`) — unlike `link_peoply_organizations` above,
which only ever looks at unions missing a `peoply_organization_id` one at a
time via Peoply's name search, this fetches everything and reports both
directions. Retired/unknown-status unions are skipped entirely — they
aren't expected to have a working Peoply link, so they're never flagged:

- site unions with no corresponding Peoply organization at all (no id set,
  and no exact name/`urlId` match either — same exact-match rule as
  `link_peoply_organizations`, see its section above for why).
- site unions whose `peoply_organization_id` no longer matches any org
  Peoply currently returns (a **stale link**) — `sync_peoply_events` would
  silently sync nothing for these, since Peoply's `/events` just returns no
  rows for an unknown `organizationId` rather than erroring, so this is the
  only thing that would ever surface it.
- Peoply organizations with no matching `UnionPage` here at all.
- site unions with no `peoply_organization_id` set, but whose title is an
  exact name/`urlId` match against a Peoply organization — not counted as
  "missing" on either side, just not linked here yet. Surfaced as its own
  kind rather than silently absorbed, specifically so there's a log to link
  from (see the admin action below, or `link_peoply_organizations --apply`).

Read-only by default — only `--create-missing` writes anything, and even
then it only ever creates a **draft** (`live=False`) `UnionPage` stub per
unmatched Peoply organization, pre-filled with its `peoply_organization_id`
and website, for an editor to review, fill in, and publish by hand rather
than going live unattended. Stubs are created under the site's single live
nb `StudentUnionCategoryPage`; pass `--parent-slug` if more than one exists.

**Warnings, not logs**: like every other command here, this uses
`self.stdout.write`/`self.style.WARNING`, not Python's `logging` module —
this project has no logger config, file handler, or Sentry wired up outside
Django's own `django.*` namespace (see `settings.py`'s `LOGGING`), so a
custom logger wouldn't actually go anywhere `self.stdout` doesn't already.
`sync_peoply_events` runs this automatically at the end of every sync (see
that command above), so these warnings land in the same terminal/`journalctl -u
sync-peoply-events.service` output its own systemd timer already produces
every 6 hours — no second schedule needed. A failure fetching Peoply's
organizations there is reported, not left to fail the event sync that
already ran.

**Persisted, not just printed**: every mismatch found is also reconciled
against the `PeoplyUnionMismatch` model (`models/event/peoply.py`) — keyed by
`(kind, identifier)` (a union's `translation_key`, or a Peoply org's own
id), so the exact same gap isn't rediscovered as "new" on every one of the
scheduled run's 6-hourly checks. A mismatch not seen before is printed as
`NEW: ...` (`self.style.ERROR`, to stand out); one already on file is
printed as `(already known) ...` (`self.style.WARNING`); one that was on
file but no longer shows up this run (a union got linked, a stub got
created, Peoply's data changed) is marked `resolved_at` and called out
separately. Read-only in the sense that this bookkeeping isn't gated by
`--create-missing` — it happens on every run, including a plain dry
report, since it's the "did we already know about this" answer the dry
report itself depends on.

**Four separate logs in Django admin, not one combined list** — each of
the model's four `kind`s (`unlinked_union`, `stale_link`, `missing_org`,
`pending_link`) gets its own proxy model and sidebar entry
(`UnionsWithoutPeoplyOrg`/`UnionsWithStalePeoplyLink`/
`PeoplyOrgsWithoutUnion`/`UnionsPendingPeoplyLink`, `models/event/peoply.py`),
each backed by a manager that filters the shared table down to just that
kind, rather than one `PeoplyUnionMismatch` listing filtered by a `kind`
dropdown — the four read as distinct problems needing distinct fixes
(never linked vs. a broken existing link vs. a Peoply org this site
doesn't know about yet vs. a match found but not yet written). All four
are superuser-only, same lockdown as `PeoplySyncLog`, and never editable —
but every row is deletable (**"Delete selected log entries"**, in each
log's Action dropdown), for pruning old/no-longer-interesting rows by
hand. Deleting is just housekeeping, not a way to silence a mismatch that's
still actually true: the next run recreates the same row from scratch the
moment it sees that same `(kind, identifier)` mismatch again (it just
won't remember the original `first_seen_at`).

Two of the four have an extra admin action beyond delete:

- **`PeoplyOrgsWithoutUnion`** — **"Create a draft UnionPage for the
  selected mismatch(es)"** — the admin-side equivalent of `--create-missing`
  above, without needing shell access. Re-fetches Peoply's current
  organization list at click time (so a mismatch that's since vanished from
  Peoply is skipped, not force-created from stale data) and marks each
  mismatch it acts on `resolved_at` immediately.
- **`UnionsPendingPeoplyLink`** — **"Link selected union(s) to their
  matched Peoply organization"** — the admin-side equivalent of
  `link_peoply_organizations --apply`, scoped to just the selected row(s).
  Also re-fetches Peoply's organizations and re-runs the exact-match check
  at click time rather than trusting the log's stored label (skips a row
  whose union already gained an id, or whose match no longer holds, rather
  than writing stale data), and marks each row it actually links
  `resolved_at` immediately.

Both re-fetch and re-verify at click time rather than trusting `label`,
and both marking `resolved_at` immediately rather than waiting for the
next scheduled `check_peoply_union_matches` run to notice.

## account_app

### cleanup_unverified_accounts

```bash
py manage.py cleanup_unverified_accounts [--dry-run]
```

Deletes signups that never confirmed their email address
(`is_active=False` until `verify_email_view` flips it — see
`account_app.views.login_views`) once they're older than
`settings.UNVERIFIED_ACCOUNT_RETENTION_DAYS` (7 days by default). Exists
for GDPR storage-limitation (Art. 5(1)(e)) — no reason to keep a
name/email on file for an account nobody ever actually claimed. A plain
delete is safe here (unlike `account_app.views.account_views.
delete_account_view`) since an unverified account can never have authored
content or hold permissions.

No task scheduler exists in this project (no Celery/django-crontab) — this
is meant to be invoked periodically from *outside* Django entirely (host
cron, or your platform's own scheduled-job feature). Nothing runs it for
you automatically. Safe to re-run. `--dry-run` lists matching accounts
without deleting them.

## core_app

### compile_translations

```bash
py manage.py compile_translations
```

Compiles `.po` translation files to `.mo` using `polib`, without needing
the system `gettext` tools (`msgfmt`) Django's own `compilemessages`
requires. Not all dev machines have `gettext` installed, and installing it
needs admin rights (common friction on Windows) — `polib` is already a
dependency via `wagtail_localize`, so this is a pure-Python drop-in
substitute for local dev. If you do have `msgfmt` available, plain
`manage.py compilemessages` works exactly the same and there's no need for
this command. Only compiles this project's own `.po` files (under each
app's `locale/`, plus `ifiplatform/locale/`), never a third-party
package's.

### announce_deploy

```bash
py manage.py announce_deploy [--minutes N] [--clear]
```

Operational, not a dev command — sets the shared "a deploy is imminent"
flag that powers the site-wide countdown banner, read by the deploy
script (`deploy/deploy.sh`) before restarting the server.
You shouldn't need to run this yourself in local dev.

### clear_cache

```bash
py manage.py clear_cache
```

Clears the site-wide cache (see `settings.py`'s `CACHES` — a `FileBasedCache`
persisted on disk under `django_cache/`, so it survives server restarts and,
notably, isn't touched by `git reset --hard` during a deploy since that
directory is untracked). Wired into `deploy/deploy.sh`, running right after
every deploy's gunicorn restart.

Exists because of a real incident: after some deploys, Wagtail's own
site-root-paths cache went stale relative to the actual page tree, and
every `Page.url` silently resolved to `None` — turning every `{% pageurl %}`
link across the site into a literal `/en/None/`-style URL for every
visitor, since this cache is shared site-wide, not per-user. Safe to run
any time; clearing a cache never loses real data, it just means the next
request recomputes whatever it needed. Also useful in local dev if you see
the same "links resolve to None" symptom after moving pages around or
reseeding the database.
