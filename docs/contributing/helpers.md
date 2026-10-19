# Helper guide for Commit for Candy

Last updated: 2026-10-20

Thanks for helping out! 🎃 This page gets you ready in about 30 minutes.
You don't need to know the code. Every issue has a 🔑 solution that only
helpers can see.

## Your job

- 🐳 **Get people's sites running.** Most questions are about setup.
- 🧭 **Walk them through it:** claim an issue → change → pull request
  (a pull request, or PR, asks for a change to be added to the project).
  Use the 🔑 solution to point them the right way, but don't paste it.
- 🔀 **Merge their pull requests**, so they get their coins and points.

## ✅ Before the event

- [ ] Make an account on the [mock site](https://halloween.ifiplattform.no)
  and ask an organiser to add you to the **Helpers** group. That makes
  the 🔑 Solution button show up.
- [ ] Set up the site on your own laptop, the same way participants do.
  Use the [setup checklist](#-setup-checklist) below. Remember where you
  got stuck: they will get stuck there too.
- [ ] Try the `ifi` commands once: `ifi fix-issue <any issue number>` →
  change a colour → `ifi test`. To throw the change away afterwards, run
  `git restore .` and `git switch main`.
- [ ] Go through the required reading below.

## 📖 Required reading (~20 min)

📖 = read it. 👀 = skim it: look at the headings so you know where to find
things when someone asks.

| | What | Why | Time |
| --- | --- | --- | --- |
| 📖 | [How the event works](../../README.md#how-the-event-works) | Claims, coins, points, limits and timers: people will ask | 3 min |
| 👀 | [Get the code](get_the_code.md) | Fork, clone and GitHub login | 3 min |
| 📖 | [Setup with Docker](setup_with_docker.md) | The setup you'll help with most | 5 min |
| 👀 | [Docker guide](docker_guide.md) | How the container works | 3 min |
| 📖 | [Restart, reopen, rebuild or reset?](docker_guide.md#restart-reopen-rebuild-or-reset) and [If something goes wrong](docker_guide.md#if-something-goes-wrong) | The fixes for most problems | 6 min |

## 📚 Recommended, if you have time

All of these are 👀 skim.

- [Make a change, step by step](../../CONTRIBUTING.md#2-make-a-change-step-by-step):
  the same steps with plain Git or GitHub Desktop, without `ifi`
- [Setup without Docker](setup_without_docker.md): the backup plan for
  laptops where Docker won't work
- [Where do I change…?](how_this_project_works.md#where-do-i-change): helps
  you read the file list in a solution
- [Tutorials](../../TUTORIALS.md): the [Git](../../TUTORIALS.md#git-and-github)
  and [Docker](../../TUTORIALS.md#docker-and-dev-containers) sections
- `ifi help` in the container terminal: short cheat sheets

## 🐳 Setup checklist

Go through this with the participant, from top to bottom.

- [ ] **Docker Desktop** is installed and **running**. On Linux, run
  `sudo systemctl enable --now docker` instead.
  ([Install the tools](setup_with_docker.md#1-install-the-tools))
- [ ] **VS Code** is installed.
- [ ] The **Dev Containers** extension (by Microsoft) is installed: press
  <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>X</kbd> (Mac:
  <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>X</kbd>), search for
  "Dev Containers" and click **Install**.
- [ ] **Fork** the repo on GitHub with the **Fork** button at the top
  right (a fork is their own copy on GitHub).
  ([Fork and clone](get_the_code.md#contributor-fork-and-clone))
- [ ] **Clone** the fork (copy it to the laptop), then go into the folder:
  ```bash
  git clone https://github.com/<their-username>/ifiplattform_halloween.git
  cd ifiplattform_halloween
  ```
  On Windows, clone inside WSL, not on `C:\`, or Docker gets very slow.
- [ ] Add **upstream** (the main repo, where the newest code is):
  ```bash
  git remote add upstream https://github.com/Creators-Guild/ifiplattform_halloween.git
  ```
  Check with `git remote -v`: `origin` is their fork, `upstream` is the
  main repo.
- [ ] Git knows who they are:
  `git config --global user.name "Their Name"` and
  `git config --global user.email "their@email"`.
  ([Log in to GitHub](get_the_code.md#log-in-to-github-once))
- [ ] Open the `ifiplattform_halloween` folder in VS Code.
- [ ] Click **Reopen in Container**. No popup? Press
  <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> and run
  `Dev Containers: Reopen in Container`. The first time takes a few
  minutes.
- [ ] http://localhost:8000 shows the Halloween site.
- [ ] `ifi test` passes in the VS Code terminal.
- [ ] They have linked their GitHub username on
  [My issues](https://halloween.ifiplattform.no/commits/), or they can't
  claim issues.

Stuck on a step? See [If something goes wrong](docker_guide.md#if-something-goes-wrong).
Docker won't work at all? Use [Setup without Docker](setup_without_docker.md).

**GitHub Desktop users:** fork on GitHub, then **File → Clone repository**
and pick the fork. Choose **"To contribute to the parent project"**, and
upstream is set up for them.

## ⌨️ The ifi commands

`ifi` commands are this project's own shortcuts. They only work in the VS
Code terminal inside the container, and each one prints the Git commands
it runs.

| Command | What it does |
| --- | --- |
| `ifi fix-issue <nr>` | Makes a branch for issue `<nr>` from the newest code. Run it again to go back to that branch. |
| `ifi status` | Checks the setup: name and email, origin/upstream, GitHub login, branch, unsaved changes, behind main, the site. Ask stuck people to run it and look at the ❌ lines |
| `ifi save "message"` | Saves (commits) every change in the whole repo, also from a subfolder. Asks for name and email the first time |
| `ifi update` | Brings the branch up to date with the newest main. On a conflict it explains the `<<<<<<<` markers; fix the files and run it again, or `ifi update --abort` |
| `ifi pull-request` | Pushes the branch and gives the pull request link, with `Closes #<nr>` already filled in. If the push fails, it says why: not logged in, wrong account, cloned the main repo instead of a fork, or an SSH address |
| `ifi undo-file <file>` | Takes a file out of the pull request (it commits and pushes for you) |
| `ifi undo-file --extra` | Takes out every file the issue doesn't list, in one go. Their version is kept on a `-backup` branch |
| `ifi test` | The quick tests. Run before a pull request. `ifi test --long` runs all of them. |
| `ifi restart-server` | Restarts the site, when a change doesn't show up or the site stopped |
| `ifi migrate` | After changing a model (rare at the event) |
| `ifi reset-server` | ⚠️ Deletes the local database and starts fresh |
| `ifi rebuild-docker` | Shows how to rebuild the container |
| `ifi help` | Cheat sheets for git, docker, django and ifi |

The usual flow for a participant:

```bash
ifi fix-issue 42
# ...make the change, check it at http://localhost:8000...
ifi test
ifi save "Short description of what you changed"
ifi pull-request
```

## 🔀 Merge checklist

Go through this for each pull request on GitHub.

- [ ] First pull request from this person? Click **Approve and run
  workflows**, so the checks start.
- [ ] The description has `Closes #<nr>`. No line means no points, so edit
  the description and add it.
- [ ] **CI** is green (the tests pass). GitHub blocks the **Merge** button
  until it is. If CI is red, open it and look for the first `FAIL:`.
  That's the real error.
- [ ] **Files check** is green: only the files the issue lists were
  changed, so you don't need to read the code.
  - 🟡 Warning: extra files were changed. Take a quick look.
  - 🔴 No `Closes #<nr>`, or made in the browser on github.com: GitHub
    blocks the merge. Add the line, or help them set up on their laptop
    instead, that's part of the event.
  - Extra files with a good idea? Small and on-topic: merge. A separate
    idea: ask them to run `ifi undo-file --extra`. Their version stays
    on a `-backup` branch, so they can make it its own pull request.
- [ ] Click **Merge**, or add the `automerge` label so it merges by itself
  when CI is done.
- [ ] The issue closes by itself. If you close one by hand, choose
  **Close as completed**, never "not planned", or nobody gets points.
- [ ] A few minutes later, check that **Actions → Deploy** is green.
  The site only updates when the deploy passes. A red deploy means
  nothing new reaches the site until someone fixes it, so tell an
  organiser.
- [ ] Press **Sync now** on the site so the points show up on the
  [Leaderboard](https://halloween.ifiplattform.no/commits/leaderboard/).

Don't merge if it's the wrong issue, the page looks broken, or GitHub
shows a merge conflict. Tell them kindly what to fix.

Organisers can **bypass** the block in an emergency. Don't use it to merge
a red ✗: one broken merge makes every later pull request red too, and
stops the site from updating.

## 🛠️ Your buttons on the site

As a helper you see extra buttons on the
[Issues page](https://halloween.ifiplattform.no/commits/issues/):

- **🔑 Solution** on every issue: which files to change and how.
- **+15 min, +30 min, No time limit, Reset** on a claimed issue, when
  someone needs more time.
- **Force release:** frees a claim, for example when someone has left.
- **Sync now:** gets the newest issues and pull requests from GitHub.

A claim stops running out once its pull request is open.

## 🚑 Common problems

| Problem | Fix |
| --- | --- |
| GitHub says "This branch has conflicts" | `ifi update`, fix the files it lists, `ifi update` again, then `ifi pull-request` |
| Someone is stuck and you don't know why | Ask them to run `ifi status` and fix the ❌ lines first |
| The container won't start | Find the real error: **View → Output → Dev Containers**. [More](docker_guide.md#if-something-goes-wrong) |
| "Port 8000 is already in use" | Another server is running. Stop it with <kbd>Ctrl</kbd>+<kbd>C</kbd> in its terminal. |
| Docker Desktop won't start (Windows) | Run `wsl --install` in PowerShell as administrator, then restart |
| Everything is slow (Windows) | The repo is on `C:\`. Clone it inside WSL instead. |
| `ifi` not found, or `ModuleNotFoundError` | The container is old: [rebuild it](docker_guide.md#restart-reopen-rebuild-or-reset) |
| A change doesn't show up | Refresh the browser, then `ifi restart-server` |
| A merged change isn't on the mock site | The deploy failed. Check **Actions → Deploy** on GitHub, and tell an organiser |
| CI is red on a pull request that only changed CSS | `main` itself may be broken. Check the newest run on `main` under **Actions**. If that's red too, it's not their fault |
| The wrong file is in the pull request | `ifi undo-file <file>`, or `ifi undo-file --extra` for all files the issue doesn't list |
| Can't claim an issue | Link the GitHub username on [My issues](https://halloween.ifiplattform.no/commits/) |
| Docker won't work at all | [Setup without Docker](setup_without_docker.md) |

## Stuck yourself?

Ask an organiser. It's fine not to know everything. 👻
