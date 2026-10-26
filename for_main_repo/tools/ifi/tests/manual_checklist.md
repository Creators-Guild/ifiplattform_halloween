# ifi: checks by hand

Last updated: 2026-10-26

`tools/ifi/tests/run` checks ifi against a fake GitHub. This list is for what
it can't fake: real GitHub logins, VS Code's pop-ups, Docker, and Windows.
Do it before ifi moves to a new repo, and after big changes.

**Before you start**
- A second GitHub account that is *not* a collaborator, so you see what a
  new student sees. Use a private browser window for it.
- A test issue in the repo, with a Type and a `### Files to change` list
  (one file), for example "Make the event cards orange" listing
  `ifiplatform/static/css/cards.css`. Use the second account's view of it.
- Warm-up (optional): `tools/ifi/tests/playground` runs the same steps on a
  fake GitHub first.

## 1. Linux, with Docker and VS Code (the main path)

| ✓ | Do | You should see |
| --- | --- | --- |
| ☐ | Fork the repo as the second account, and clone the fork with HTTPS | A folder with the repo |
| ☐ | Open it in VS Code → **Reopen in Container** | The site starts; no error in the terminal |
| ☐ | Open the first terminal (Terminal → New Terminal) after the build log is done | "Checking your setup..." and either ✅ Setup OK or only ❌ lines |
| ☐ | Open a second terminal | No new check: "✅ Setup OK (checked <date> <time>)" and "Check again?  →  ifi check" |
| ☐ | Ports panel | One port: 8000, labelled **Website**, green dot, shows runserver |
| ☐ | `ifi check` | No ❌. If "Not logged in": run `git push`, click **Allow**, log in, run it again |
| ☐ | `ifi fix-issue <test issue>` | The issue's title; a branch named `<type>/<few-words>` |
| ☐ | Change the file, `ifi save "Orange cards"` | The file under "Committing these files" |
| ☐ | `ifi pull-request`, Ctrl+click the link | GitHub's "Open a pull request" page, with `Closes #<nr>` filled in |
| ☐ | Open the pull request | The template in the description; CI runs |
| ☐ | Change a file the issue doesn't list, save, pull-request | The file shows in the pull request's Files changed |
| ☐ | `ifi undo-file --extra`, answer y | The extra file goes back, and is gone from Files changed |
| ☐ | Make a commit on main that changes the same line (as yourself, in another clone or on GitHub) | |
| ☐ | `ifi check` | "has 1 new commit(s)" and "You'll likely get a conflict in: ..." |
| ☐ | `ifi update`, answer y to help | The conflict explanation; VS Code shows Accept buttons on the file |
| ☐ | Fix the file, `ifi update`, then `ifi pull-request` | "✓ Replaced your branch on GitHub with the updated one", and the pull request shows the new commits |
| ☐ | Press **Update branch** on the pull request on GitHub, then make a change and `ifi save` + `ifi pull-request` | "Your branch on GitHub has commits that aren't on your computer", with the `git pull --rebase` line. Run it, then pull-request works |
| ☐ | Merge the pull request (as yourself), then `ifi check` and `ifi cleanup` (still on the branch) | check: "Your pull request … is merged". cleanup: switches you to main, deletes the branch here and on the fork |
| ☐ | `command -v gh` in the container terminal | Nothing: the GitHub CLI isn't in the container |
| ☐ | Computer that logs in with gh, the other account *not* selected in gh: `ifi account switch <other>` | The gh message with `gh auth switch --user <other>`; no password prompt; `git remote -v` unchanged |
| ☐ | On the computer: `gh auth switch --user <other>`. In the container: `ifi account switch <other>`, then `ifi save` + `ifi pull-request` | "✅ Logged in as <other>"; the commit on GitHub shows that account |
| ☐ | `ifi account switch` (no name), and `gh auth switch` on the computer | "Account picked: your computer's usual one" |
| ☐ | Windows (Git for Windows): `ifi account switch <other>` | A login window opens; after logging in, "✅ Logged in as <other>" |
| ☐ | Mac without Git Credential Manager or gh: `ifi account switch <other>` | "no saved login", with the GitHub CLI steps; nothing changed |
| ☐ | Without Docker, on a computer with gh: `./ifi account switch <other>` | Offers to log in with gh and select the account, then "✅ Logged in as <other>" |
| ☐ | `ifi help`, type 1 | The Git cheat sheet |
| ☐ | `ifi restart-server` | "Restarting the server"; the site is back after a reload |
| ☐ | `ifi reset-database`, type yes | The test content again; log in with admin / admin |
| ☐ | `ifi rebuild-docker`, then do what it says | VS Code reopens in a new container; the site works |

**Wrong-setup checks** (put each one back afterwards):

| ✓ | Do | `ifi check` should say |
| --- | --- | --- |
| ☐ | `git remote set-url origin git@github.com:<you>/<repo>.git` | ⚠️ SSH address, with the set-url line to switch back, and no second ❌ "Can't use SSH here" |
| ☐ | `git remote remove upstream` | ❌ No 'upstream' remote, with the add line |
| ☐ | Clone the main repo (not the fork) as the second account, `ifi fix-issue`, save, `ifi pull-request` | Only the ❌ "You cloned the main repo, but <account> can't push to it", with fork steps; no ✅ "origin is the main repo … collaborator" and no "upstream isn't needed" |
| ☐ | Clone the main repo as a collaborator, `ifi check` | ✅ "origin is the main repo … as a collaborator" and ✅ "upstream isn't needed", no ❌ |

## 2. Linux, without Docker

| ✓ | Do | You should see |
| --- | --- | --- |
| ☐ | Follow `docs/contributing/setup_without_docker.md` | The site at http://localhost:8000 |
| ☐ | `./ifi install`, open a new terminal | `ifi` works; Tab completes `ifi up` to `ifi update` |
| ☐ | `./ifi install` again | "Already in ~/.bashrc" |
| ☐ | `scp` or `rsync` to this computer, or `bash -c true` | Prints nothing extra |
| ☐ | `ifi check` | ⚠️ Not inside the Docker container (fine), and nothing else odd |
| ☐ | `ifi test` | Runs with the venv's Python, without activating it |
| ☐ | `ifi reset-database` | Asks you to stop the server; deletes and refills db.sqlite3 |
| ☐ | `ifi restart-server` | Explains Ctrl+C and runserver |

## 3. Windows

| ✓ | Do | You should see |
| --- | --- | --- |
| ☐ | Clone inside WSL (Ubuntu terminal), `code .`, Reopen in Container | Same as part 1, and the site reloads on save |
| ☐ | Clone to `C:\...` instead, Reopen in Container | Works, just slower; `ifi check` has no ❌ |
| ☐ | On a `C:\` clone (Git for Windows sets `core.autocrlf=true`), in the container: `ifi check` | No "bad interpreter" or `$'\r'` errors |
| ☐ | Git Bash in the repo folder: `./ifi check` | Runs on Windows itself, with your Windows GitHub login |
| ☐ | Docker running outside VS Code (`docker compose up -d`), Git Bash: `./ifi test` | Runs inside the container (it says so in the command) |
| ☐ | PowerShell in the repo folder: `.\ifi check` | Same as Git Bash |
| ☐ | Command Prompt: `ifi check` | Same as Git Bash |
| ☐ | Git Bash: `./ifi install`, new Git Bash window | `ifi` works without `./` |
| ☐ | `ifi fix-issue` with a title with æøå | The branch name has ae/o/a, no odd characters |

## Write down
Anything that confused you, even if it worked: the wording, a missing next
step, a wait with no message. Those are bugs too, for beginners.
