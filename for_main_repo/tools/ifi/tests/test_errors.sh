# What ifi says when GitHub refuses a fetch or push (explain_git_error in
# common.sh), fed with the messages GitHub really gives.

NL=$'\n'

# explain <remote> <Git's message>: sets OUT and STATUS. Answers "n" when
# asked to switch to HTTPS.
explain() {
    OUT="$(cd "$SANDBOX/work" && printf 'n\n' | bash -c 'source "$1/common.sh"; explain_git_error "$2" "$3"' _ "$TOOLS" "$1" "$2" 2>&1)"
    STATUS=$?
}

t_error_ssh_offers_https() {
    clone_as contributor
    git remote set-url origin "git@github.com:$STUDENT/$NAME.git"
    explain origin $'git@github.com: Permission denied (publickey).\nfatal: Could not read from remote repository.'
    fails
    has "'origin' uses an SSH address"
    has "git remote set-url origin https://github.com/$STUDENT/$NAME.git"
}

t_error_not_logged_in() {
    clone_as contributor
    explain origin "fatal: could not read Username for 'https://github.com': terminal prompts disabled"
    has "You're not logged in to GitHub here."
}

t_error_password_instead_of_a_login() {
    clone_as contributor
    explain origin "remote: Invalid username or token. Password authentication is not supported for Git operations.${NL}fatal: Authentication failed for 'https://github.com/$STUDENT/$NAME.git/'"
    has "You're not logged in to GitHub here."
}

t_error_pushing_to_the_main_repo_without_access() {
    clone_as collaborator
    explain origin "remote: Permission to $MAIN.git denied to kari-n.${NL}fatal: unable to access 'https://github.com/$MAIN.git/': The requested URL returned error: 403"
    has "You cloned the main repo, but only collaborators can push to it."
    has "git remote add origin https://github.com/kari-n/$NAME.git"
}

t_error_logged_in_as_someone_else() {
    clone_as contributor
    explain origin "remote: Permission to $STUDENT/$NAME.git denied to old-account.${NL}fatal: unable to access 'https://github.com/$STUDENT/$NAME.git/': The requested URL returned error: 403"
    has "GitHub says you're logged in as old-account"
}

t_error_fork_not_found() {
    clone_as contributor
    explain origin "remote: Repository not found.${NL}fatal: repository 'https://github.com/$STUDENT/$NAME.git/' not found"
    has "GitHub can't find https://github.com/$STUDENT/$NAME.git."
}

t_error_branch_on_github_moved_on() {
    clone_as contributor
    git switch --quiet -c bug/x
    explain origin $' ! [rejected]        HEAD -> bug/x (fetch first)\nerror: failed to push some refs'
    has "Your branch on GitHub has commits that aren't on your computer"
    has "git pull --rebase origin bug/x"
}

t_error_no_internet() {
    clone_as contributor
    explain origin "fatal: unable to access 'https://github.com/x/y.git/': Could not resolve host: github.com"
    has "Git couldn't reach GitHub."
}

# explain_login <name>: what ifi account switch says when the computer gives
# no login for <name>. Sets OUT and STATUS.
explain_login() {
    OUT="$(cd "$SANDBOX/work" && bash -c 'source "$1/common.sh"; explain_account_login "$2"' _ "$TOOLS" "$1" 2>&1)"
    STATUS=$?
}

t_error_account_login_with_gh() {
    clone_as contributor
    git config --global --add credential.https://github.com.helper ""
    git config --global --add credential.https://github.com.helper '!/usr/bin/gh auth git-credential'
    explain_login octocat
    fails
    has "logs in to GitHub with the GitHub CLI (gh)"
    has "gh auth switch --user octocat"
    has "then here: ifi account switch octocat"
    has "Nothing changed."
}

t_error_account_login_with_credential_manager() {
    clone_as contributor
    git config --global credential.helper manager
    explain_login octocat
    has "The login window was closed"
    has "ifi account switch octocat, and log in as octocat in the window"
}

t_error_account_login_with_nothing_that_opens_a_window() {
    clone_as contributor
    git config --global credential.helper osxkeychain
    explain_login octocat
    has "no saved login for octocat"
    has "install the GitHub CLI (cli.github.com)"
    has "On Windows?"
}
