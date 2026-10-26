# Get the code

Last updated: 2026-10-26

The first step, before you set up the site. You get a copy of the repo on
your own computer: a folder called `IfiPlatform`. How you get it
depends on one thing.

## Which one are you?

| You are a… | If… | You |
| --- | --- | --- |
| **Contributor** | You don't have write access to the repo. This is most people. | [Fork, then clone your fork](#contributor-fork-and-clone) |
| **Collaborator** | You were given write access to the repo. | [Clone the repo directly](#collaborator-clone) |

**Not sure? You're a contributor.**

**On Windows, and going to use Docker?** You can clone to a windows folder, but WSL is faster. Clone inside WSL, not to a drive like `C:\`: open the Ubuntu terminal, clone there, and run `code .` in the repo folder. Docker is much faster that way. GitHub Desktop always clones to a Windows folder, so the site runs slower with it, but it still works.

**Use the HTTPS address** (`https://github.com/...`), as below, not the SSH one (`git@github.com:...`). HTTPS works in the container without any setup, because VS Code shares your GitHub login with it. Already cloned with SSH? `ifi pull-request` offers to switch it for you, or run `git remote set-url origin https://github.com/<your-username>/IfiPlatform.git`.

**Rather click than type commands?** Install [GitHub Desktop](https://desktop.github.com/). Each section below says how to do it there.

## Contributor: fork and clone
**Fork** the repo on GitHub (the "Fork" button at the top right), then clone your fork and connect it to the main repo:
```bash
git clone https://github.com/<your-username>/IfiPlatform.git
cd IfiPlatform
git remote add upstream https://github.com/Creators-Guild/IfiPlatform.git
```
`origin` is now your own fork, which is where you push. `upstream` is the main repo, where you get everyone else's changes:

![Fork and clone: upstream is our repo, origin is your fork, and your clone is on your computer](images/fork_and_clone.svg)

You only fork and clone once. After that the work goes in a loop: get the latest code from `upstream`, push your branch to `origin`, and open a pull request back to `upstream`.

**With GitHub Desktop:** fork the repo on GitHub as above, then in GitHub Desktop choose **File → Clone repository** and pick your fork. When it asks how you plan to use the fork, choose **"To contribute to the parent project"**. That sets up the connection to the main repo for you.

## Collaborator: clone
Clone the main repo directly. You don't need a fork:
```bash
git clone https://github.com/Creators-Guild/IfiPlatform.git
cd IfiPlatform
```
Don't add an `upstream` remote. `origin` already is the main repo, so you use `origin` wherever the guides say `upstream`:

![Clone as a collaborator: origin is our repo, you push your branch to it and open a pull request into main](images/clone_collaborator.svg)

You only clone once. After that the work goes in a loop: get the latest code from `origin`, push your branch to `origin`, and open a pull request from your branch into `main`. The commands are listed in [For collaborators](collaborators.md).

**With GitHub Desktop:** choose **File → Clone repository** and pick `Creators-Guild/IfiPlatform`. It doesn't ask about a fork.

## Log in to GitHub (once)
Cloning needs no login, but committing and pushing do. Do this once, on your own computer. If you use Docker, VS Code shares this login with the container, so don't do it inside the container.

**1. Tell Git who you are.** Otherwise your first `git commit` stops with "Please tell me who you are":
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```
Don't want your email to be public in the commits? Use the private no-reply address from GitHub → **Settings → Emails**. It looks like `12345678+username@users.noreply.github.com`.

**2. Log in for pushing.** GitHub doesn't accept your password in the terminal: you get `Authentication failed` even when it's right. Log in through the browser instead. VS Code does this for you: the first time you run `git push` in VS Code's terminal, a pop-up asks you to sign in to GitHub. Click **Allow**, log in in the browser window that opens, and go back to VS Code. You only do this once.

The same pop-up comes if you push from VS Code's **Source Control** panel instead. That's the panel for Git with buttons instead of commands. Open it with the branch-shaped icon in the left sidebar, or <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>G</kbd> (Mac: <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>G</kbd>).

Other ways that do the same:
- **Windows:** Git for Windows opens a GitHub login window the first time you push. Choose **Sign in with your browser**.
- **GitHub CLI**, if you have it: run `gh auth login`, pick **GitHub.com**, **HTTPS** and **Login with a web browser**.

**Logged in as the wrong user?** The push fails with `Permission to Creators-Guild/… denied to <someone else>` or a `403`. Your computer remembers another GitHub account. Remove the saved login, and the next push asks you to log in again:
- **Mac:** open **Keychain Access**, search for `github.com`, and delete the entry.
- **Windows:** open **Credential Manager → Windows Credentials**, and remove `git:https://github.com`.
- **GitHub CLI:** `gh auth switch`, or `gh auth logout` and then `gh auth login`.

Want to push as a different account in this repo only, and keep your computer's usual login for everything else? Run `ifi account switch <username>`. [Docker guide](docker_guide.md#another-github-account-in-the-container) explains it.

**GitHub Desktop** has its own login (**Settings → Accounts**, on Windows **File → Options → Accounts**). It doesn't log in the terminal, and the terminal login doesn't log in GitHub Desktop.

## Next: run the site
You have the code. Now get the site running:
- [Setup with Docker](setup_with_docker.md) (recommended)
- [Setup without Docker](setup_without_docker.md)
