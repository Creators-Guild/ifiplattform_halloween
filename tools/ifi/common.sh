# Shared by the ifi commands. Sourced, not run.

MAIN_REPO="Creators-Guild/ifiplattform_halloween"

# Prints a command, then runs it, so people see the real Git behind ifi.
run() {
    printf '+ %s\n' "$*"
    "$@"
}

die() {
    printf '%s\n' "$@" >&2
    exit 1
}

# "owner/repo" from a GitHub remote, for both https and ssh URLs.
repo_of() {
    git config --get "remote.$1.url" |
        sed -E 's#^(https://github\.com/|ssh://git@github\.com/|git@github\.com:)##; s#\.git$##; s#/$##'
}

# Git refuses to commit without a name and email ("Please tell me who you
# are"). Asks once and saves them for every repo on this computer (or in
# this container).
ensure_identity() {
    local name email
    name="$(git config user.name || true)"
    email="$(git config user.email || true)"
    [[ -n "$name" && -n "$email" ]] && return
    echo "Git needs your name and email once. They're written into your commits."
    echo "Want your email kept private? Use the no-reply address from GitHub ->"
    echo "Settings -> Emails (it looks like 12345678+username@users.noreply.github.com)."
    while [[ -z "$name" ]]; do
        read -r -p "Your name: " name || die ""
    done
    while [[ ! "$email" =~ ^[^@[:space:]]+@[^@[:space:]]+$ ]]; do
        read -r -p "Your email: " email || die ""
    done
    run git config --global user.name "$name"
    run git config --global user.email "$email"
}

# What kind of failure Git's message ($1) is: ssh, login, denied, notfound,
# behind or other. Shared by explain_git_error and `ifi status`.
git_error_kind() {
    if grep -qiE "cannot run ssh|ssh: not found|Permission denied \(publickey\)|Host key verification failed" <<<"$1"; then
        echo ssh
    elif grep -qiE "could not read Username|Authentication failed|terminal prompts disabled|Invalid username or (password|token)" <<<"$1"; then
        echo login
    elif grep -qiE "Permission to .* denied to|returned error: 403|error: 403" <<<"$1"; then
        echo denied
    elif grep -qi "Repository not found" <<<"$1"; then
        echo notfound
    elif grep -qiE "non-fast-forward|fetch first|\[rejected\]" <<<"$1"; then
        echo behind
    else
        echo other
    fi
}

# The account name in "Permission to X denied to <account>", if any.
denied_user() {
    sed -nE 's/.*Permission to .* denied to ([^ .]+).*/\1/p' <<<"$1" | head -n 1
}

# Explains a failed fetch or push in plain words. $1 is the remote, $2 is
# what Git printed. Always exits.
explain_git_error() {
    local remote="$1" err="$2" url repo kind
    url="$(git remote get-url "$remote" 2>/dev/null || true)"
    repo="$(repo_of "$remote")"
    kind="$(git_error_kind "$err")"
    printf '%s\n\n' "$err" >&2

    if [[ "$kind" == ssh ]]; then
        echo "'$remote' uses an SSH address ($url), and SSH doesn't work here." >&2
        echo "HTTPS works without any setup, because VS Code shares your GitHub login." >&2
        local answer=""
        read -r -p "Switch '$remote' to https://github.com/$repo.git? (y/n) " answer || true
        if [[ "$answer" =~ ^[YyJj] ]]; then
            run git remote set-url "$remote" "https://github.com/$repo.git"
            die "Done. Run the same ifi command again."
        fi
        die "Nothing changed. To switch later:" \
            "  git remote set-url $remote https://github.com/$repo.git"
    fi

    if [[ "$kind" == login ]]; then
        die "You're not logged in to GitHub here." \
            "In VS Code: run 'git push' once in the VS Code terminal and click Allow in the" \
            "popup, then log in in the browser. Without VS Code: push from a terminal on" \
            "your own computer instead. More: docs/contributing/get_the_code.md#log-in-to-github-once"
    fi

    if [[ "$kind" == denied ]]; then
        local user
        user="$(denied_user "$err")"
        if [[ "${repo,,}" == "${MAIN_REPO,,}" && "$remote" == origin ]]; then
            die "You cloned the main repo, but only collaborators can push to it." \
                "Push to your own fork instead:" \
                "  1. Fork the repo on GitHub (the Fork button on github.com/$MAIN_REPO)" \
                "  2. Point Git at it:" \
                "       git remote rename origin upstream" \
                "       git remote add origin https://github.com/${user:-<your-username>}/${MAIN_REPO#*/}.git" \
                "  3. Run the same ifi command again."
        fi
        die "GitHub says you're logged in as ${user:-someone else}, and that account can't push to $repo." \
            "Logged in with the wrong account? Remove the saved login, and the next push asks again:" \
            "  Mac:        Keychain Access -> search github.com -> delete it" \
            "  Windows:    Credential Manager -> Windows Credentials -> remove git:https://github.com" \
            "  GitHub CLI: gh auth switch" \
            "More: docs/contributing/get_the_code.md#log-in-to-github-once"
    fi

    if [[ "$kind" == notfound ]]; then
        die "GitHub can't find $url." \
            "Did you fork the repo yet? Is the username in the address right? See it with:" \
            "  git remote -v"
    fi

    if [[ "$kind" == behind ]]; then
        die "Your branch on GitHub has commits that aren't on your computer" \
            "(for example from GitHub's Update branch button). Get them first, then try again:" \
            "  git pull --rebase origin $(git branch --show-current)"
    fi

    die "Git couldn't reach GitHub. The message above says why. Ask a helper if it's unclear."
}

# Runs a git command that talks to GitHub (fetch, push). Shows it like run,
# and explains the error if it fails. $1 is the remote it talks to.
git_or_explain() {
    local remote="$1" err
    shift
    printf '+ git %s\n' "$*"
    if ! err="$(git "$@" 2>&1)"; then
        explain_git_error "$remote" "$err"
    fi
    [[ -n "$err" ]] && printf '%s\n' "$err"
    return 0
}

# Sets $base: the remote that holds the main repo. Collaborators cloned it
# directly (origin). Contributors cloned their fork, so it's upstream, which
# is added here if they skipped that step in get_the_code.md.
find_base() {
    local origin_repo
    origin_repo="$(repo_of origin)"
    if [[ "${origin_repo,,}" == "${MAIN_REPO,,}" ]]; then
        base=origin
    else
        if ! git remote get-url upstream >/dev/null 2>&1; then
            run git remote add upstream "https://github.com/$MAIN_REPO.git"
        fi
        base=upstream
    fi
}

# Fetches the main repo's newest code into $base/main.
fetch_base() {
    git_or_explain "$base" fetch --quiet "$base"
}

git rev-parse --git-dir >/dev/null 2>&1 || die "Run this inside the project folder."
