# ifi account, and why the container has no gh

Last updated: 2026-10-26
Covers: tools/ifi/account, Dockerfile.dev, tools/ifi/common.sh, tools/ifi/check

## Why no GitHub CLI in the container

In the Halloween mock repo, where ifi was built, `ifi account` first used
`gh auth login` / `gh auth switch` inside the container, with `credential.https://github.com.helper '!gh auth git-credential'`
in Dockerfile.dev and a `gh-config` volume on `/home/dev/.config/gh` so the
login survived rebuilds. With no keyring in the container, gh saves its token
as plain text in `hosts.yml`. That token has the `repo` scope (every repo the
person can reach) and doesn't expire. Everything runs as user `dev`, including
the docker-compose start command (`migrate`, `seed_dev_data`,
`runserver`), and that command runs code from whatever branch is checked out.
So checking out someone's pull request could quietly leak the token. gh, its
credential line and the volume were removed there (2026-10-25) before ifi
came to this repo. Don't add them.

## How `ifi account switch <name>` picks the account instead

- The username goes into origin's address:
  `https://<name>@github.com/<owner>/<repo>.git`. Git passes it to the
  credential helper. In the container, that's VS Code's helper, which forwards
  the request to the host's `git credential fill`. Without VS Code
  (`docker compose exec`) there's no forwarding, so pushing doesn't work
  there anyway. Without Docker, the host's git reads the same address.
- **Test first, change after** (`switch_to` in tools/ifi/account). It does a
  dry-run push straight to the address with the name
  (`try_login`: `git push --dry-run` to `refs/heads/ifi-check-login`, like
  ifi check step 6). Only if that works does it set origin and
  `user.name`/`user.email`. Any failure says "Nothing changed". The
  timeout is 120 s, because GCM opens a browser and waits.
  `GIT_TERMINAL_PROMPT=0` turns git's password prompt (GitHub rejects
  passwords) into an error that `git_error_kind` classifies as `login`.
- Whether the host gives a login depends on its tool (2026-10-25):
  - **GCM** (Git for Windows' default; some Macs): keeps one login per
    username and opens a browser for a new one. This just works.
  - **gh** (`gh auth git-credential`): checked in cli/cli
    `pkg/cmd/auth/gitcredential/helper.go`. It takes the *active* account's
    token. If the requested username differs, it returns SilentError (no
    credential). It never starts a login. So the username must equal gh's
    selected account on the host, and switching means `gh auth switch` there
    too. `gh_here` does that for the user, but only without Docker (gh on
    the host is reachable).
  - **osxkeychain / nothing**: no browser, so there's no way to add a new
    account from git. The message suggests installing gh.
- On a gh host, asking for a username gh refuses doesn't just fail: the
  host's git falls back to its askpass (seen: KDE's `/usr/bin/ksshaskpass`),
  and a password window pops up on the host. `GIT_TERMINAL_PROMPT=0` can't
  stop it: it only covers terminal prompts, and only in the container. So
  `gh_selects_other` (common.sh) first asks *without* a username. gh answers
  that with its selected account, no window. If that's someone else, the
  login is never tried: in `switch_to`, `show`, ifi check step 6, and pushes
  to origin in `git_or_explain`. Still open: if the host's gh has nobody
  logged in at all, even the nameless ask pops the window.
- `login_tool` (common.sh) picks which message `explain_account_login` shows.
  It reads `credential.helper` and `credential.https://github.com.helper`.
  In the container, those come from the host's `~/.gitconfig`, which VS Code
  copies in at container creation (that's how a host gh helper shows up
  there). Git for Windows and Xcode git set their helper in *system* config,
  which isn't copied, so Windows/Mac hosts often look `unknown`. That's
  harmless: the dry-run decides success, and `login_tool` only picks the
  wording.
- The copied host gh helper lines also make the container's git try a missing
  `/usr/bin/gh` before VS Code's helper. That only prints noise.
- `ifi account switch` with no name strips the username and unsets the
  repo-level `user.name`/`user.email`.
- Only the login changes, never which repo origin points at (the user chose
  this). `denied`/`notfound` from the dry-run means that account can't push
  to origin.

## Commit name and email

The login and the commit identity are separate settings. `profile_of` reads
the public API `GET /users/<name>`, and `switch_to` sets repo-level
`user.name`/`user.email` from it:
`name` (or `login`) and `<id>+<login>@users.noreply.github.com`. It uses the
same `$PY` + urllib + `IFI_GITHUB_API` pattern as fix-issue, so the tests
serve `$API_DIR/users/<name>` from the fake API (tests/lib.sh). The `.git`
folder is shared with the host, so a clone there pushes and signs as this
account too.

## Knock-on changes elsewhere

- `repo_of` (common.sh) and ifi check's step 4 accept `https://name@github.com/`.
  Any new code that matches origin URLs must too.
- `github_login` (common.sh) sends `url=<origin url>` to `git credential fill`
  so the picked username counts. It ends in `|| true` because callers run
  under `set -e` and expect empty output, not a failure, when nobody is
  logged in.
- ifi check step 6b warns only when origin names a username and
  `user.email` doesn't contain it.
- ifi check step 6, `login` case: when origin names a username, it points to
  `ifi account switch <name>` (which explains per tool), not the VS Code popup.
- Tests: tests/lib.sh maps `https://octocat@github.com/` to the sandbox
  remotes, so switch tests never reach real GitHub. Use `octocat` for
  switches that should succeed.
