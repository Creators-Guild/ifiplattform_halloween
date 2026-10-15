# Get the code

Last updated: 2026-10-15

The first step, before you set up the site. You get a copy of the repo on
your own computer: a folder called `ifiplattform_halloween`. How you get it
depends on one thing.

## Which one are you?

| You are a… | If… | You |
| --- | --- | --- |
| **Contributor** | You don't have write access to the repo. This is most people. | [Fork, then clone your fork](#contributor-fork-and-clone) |
| **Collaborator** | You were given write access to the repo. | [Clone the repo directly](#collaborator-clone) |

**Not sure? You're a contributor.**

**On Windows, and going to use Docker?** Clone inside WSL, not to a drive like `C:\`: open the Ubuntu terminal, clone there, and run `code .` in the repo folder. Docker is much faster that way. GitHub Desktop always clones to a Windows folder, so the site runs slower with it, but it still works.

**Rather click than type commands?** Install [GitHub Desktop](https://desktop.github.com/). Each section below says how to do it there.

## Contributor: fork and clone
**Fork** the repo on GitHub (the "Fork" button at the top right), then clone your fork and connect it to the main repo:
```bash
git clone https://github.com/<your-username>/ifiplattform_halloween.git
cd ifiplattform_halloween
git remote add upstream https://github.com/Creators-Guild/ifiplattform_halloween.git
```
`origin` is now your own fork, which is where you push. `upstream` is the main repo, where you get everyone else's changes:

![Fork and clone: upstream is our repo, origin is your fork, and your clone is on your computer](images/fork_and_clone.svg)

You only fork and clone once. After that the work goes in a loop: get the latest code from `upstream`, push your branch to `origin`, and open a pull request back to `upstream`.

**With GitHub Desktop:** fork the repo on GitHub as above, then in GitHub Desktop choose **File → Clone repository** and pick your fork. When it asks how you plan to use the fork, choose **"To contribute to the parent project"**. That sets up the connection to the main repo for you.

## Collaborator: clone
Clone the main repo directly. You don't need a fork:
```bash
git clone https://github.com/Creators-Guild/ifiplattform_halloween.git
cd ifiplattform_halloween
```
Don't add an `upstream` remote. `origin` already is the main repo, so you use `origin` wherever the guides say `upstream`:

![Clone as a collaborator: origin is our repo, you push your branch to it and open a pull request into main](images/clone_collaborator.svg)

You only clone once. After that the work goes in a loop: get the latest code from `origin`, push your branch to `origin`, and open a pull request from your branch into `main`. The commands are listed in [For collaborators](collaborators.md).

**With GitHub Desktop:** choose **File → Clone repository** and pick `Creators-Guild/ifiplattform_halloween`. It doesn't ask about a fork.

## Next: run the site
You have the code. Now get the site running:
- [Setup with Docker](setup_with_docker.md) (recommended)
- [Setup without Docker](setup_without_docker.md)
