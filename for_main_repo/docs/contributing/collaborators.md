# For collaborators

Last updated: 2026-10-20

You're a **collaborator** if you have write access to the main repo. Then
you don't need a fork: you clone the main repo and push your branches
straight to it. Everything else (issues, pull requests, reviews) works the
same as for everyone else in [CONTRIBUTING.md](../../CONTRIBUTING.md).

Not sure if you have write access? You probably don't. Use the normal
[fork setup](get_the_code.md#contributor-fork-and-clone).

## What's different

| | Contributors | Collaborators |
| --- | --- | --- |
| Get the code | Fork, then clone your fork | Clone the main repo |
| Remotes | `origin` = your fork, `upstream` = main repo | `origin` = main repo, no `upstream` |
| Push your branch to | Your fork | The main repo |
| Pull requests | From your fork to the main repo | From your branch to `main`, inside the main repo |
| Merging | A Committer reviews and merges | A Committer reviews and merges |
| Issues | Open and comment | Also label, assign and close |

## Set up

1. [Get the code as a collaborator](get_the_code.md#collaborator-clone):
   clone the main repo, no fork.
2. Run the site with [Docker](setup_with_docker.md) or
   [without Docker](setup_without_docker.md), as everyone else does.

## Every command, with origin

The guides use `upstream`. You use `origin` instead:

| Step | Guide says | You run |
| --- | --- | --- |
| Make a branch | `git fetch upstream`<br>`git switch -c <type>/<few-words> upstream/main` | `git fetch origin`<br>`git switch -c <type>/<few-words> origin/main` |
| Update your branch | `git fetch upstream`<br>`git rebase upstream/main` | `git fetch origin`<br>`git rebase origin/main` |
| Push | `git push -u origin <branch>` | The same |

In GitHub Desktop, base new branches on **origin/main**.

## Good to know

- **Never push straight to `main`.** Always use a branch and a pull
  request, so a Committer can review it.
- **Branches are shared.** Everyone with write access sees your branches.
  Use the `<type>/<few-words>` names, and delete your branch after it's
  merged (GitHub offers a button on the pull request).
- **Getting write access:** ask a Committer. See
  [Who can contribute](../../CONTRIBUTING.md#who-can-contribute).
