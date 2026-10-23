# Shared by the ifi commands. Sourced, not run.

MAIN_REPO="Creators-Guild/ifiplattform_halloween"

# The scripts also run without Docker: on a Mac (bash 3.2, so no ${x,,} or
# mapfile), and in Git Bash on Windows (often `python` but no `python3`).

# Lower case, for comparing GitHub names (they ignore case).
lower() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# A Python for the small helper snippets: python3, or python where that's
# all there is (Windows' python3 is often a stub that only opens the Store).
if python3 -c '' >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

# True inside the Docker dev container.
in_container() {
    [[ -f /.dockerenv || "${USE_POSTGRES:-}" == True ]]
}

# Runs a command with a time limit where `timeout` exists (not on a Mac).
with_timeout() {
    if command -v timeout >/dev/null 2>&1; then
        timeout "$@"
    else
        shift
        "$@"
    fi
}

# Sets $DJANGO_PY: the Python that has Django. In the container that's
# python; without Docker it's the project's venv, found by itself, so you
# don't have to activate it.
find_django_python() {
    local top
    top="$(git rev-parse --show-toplevel)"
    DJANGO_PY=python
    in_container && return
    local candidate
    for candidate in venv/bin/python .venv/bin/python venv/Scripts/python.exe .venv/Scripts/python.exe; do
        if [[ -x "$top/$candidate" ]]; then
            DJANGO_PY="$top/$candidate"
            return
        fi
    done
    "$DJANGO_PY" -c 'import django' >/dev/null 2>&1 ||
        die "Can't find a Python with Django. Make the venv first: docs/contributing/setup_without_docker.md"
}

# Colours only on a terminal, so pipes and logs get plain text.
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    C_BOLD=$'\e[1m' C_CMD=$'\e[36m' C_DIM=$'\e[2m' C_OFF=$'\e[0m'
else
    C_BOLD="" C_CMD="" C_DIM="" C_OFF=""
fi

# Every command ifi runs is shown as a numbered step, so people see the real
# Git behind ifi and can type it themselves later. GIT_DONE collects the git
# commands for git_recap.
STEP=0
GIT_DONE=()

# The command as you'd type it: words with spaces or quotes in "double quotes".
shown() {
    local out="" a
    for a in "$@"; do
        if [[ -z "$a" || "$a" =~ [^A-Za-z0-9_./:@%+=,~^-] ]]; then
            a="${a//\\/\\\\}"
            a="${a//\"/\\\"}"
            a="${a//\$/\\\$}"
            a="${a//\`/\\\`}"
            a="\"$a\""
        fi
        out+="${out:+ }$a"
    done
    printf '%s' "$out"
}

# One numbered step: what it does, then the command. --quiet only keeps
# ifi's own output short, so it isn't shown (nor in git_recap).
step() {
    local why="$1"
    shift
    STEP=$((STEP + 1))
    printf '\n%s%d. %s%s\n' "$C_BOLD" "$STEP" "$why" "$C_OFF"
    printf '   %s$ %s%s\n' "$C_CMD" "$(shown "$@" | sed 's/ --quiet//g')" "$C_OFF"
}

# Git's own output, under a label so it's clear Git is talking, not ifi.
git_output() {
    [[ -n "$1" ]] || return 0
    printf '   %sGit output:%s\n' "$C_DIM" "$C_OFF"
    printf '%s\n' "$1" | sed 's/^/     /'
}

# run "what it does" command...: shows the step, then runs it. Git's output
# goes under "Git output:". Other commands (Django) print straight through,
# since makemigrations can ask questions. A leading `env VAR=x` is run but
# not shown.
run() {
    local why="$1"
    shift
    local cmd=("$@")
    if [[ "$1" == env ]]; then
        cmd=("${@:2}")
        while [[ "${cmd[0]}" == *=* ]]; do cmd=("${cmd[@]:1}"); done
    fi
    step "$why" "${cmd[@]}"
    if [[ "${cmd[0]}" != git ]]; then
        "$@"
        return
    fi
    GIT_DONE+=("$(shown "${cmd[@]}")")
    local out status=0
    out="$("$@" 2>&1)" || status=$?
    git_output "$out"
    return $status
}

# "In plain Git, this was:" with every git command this run used.
git_recap() {
    [[ ${#GIT_DONE[@]} -gt 0 ]] || return 0
    echo
    echo "In plain Git, this was:"
    printf '  %s\n' "${GIT_DONE[@]}" | sed 's/ --quiet//g'
}

# The "What now?" options: pairs of situation and what to do, arrows lined up.
# An empty situation continues the line above, without an arrow.
choices() {
    local width=0 i v arrow
    for ((i = 1; i <= $#; i += 2)); do
        v="${!i}"
        [[ ${#v} -gt $width ]] && width=${#v}
    done
    while [[ $# -gt 0 ]]; do
        arrow="→"
        [[ -z "$1" ]] && arrow=" "
        printf '  %-*s  %s  %s\n' "$width" "$1" "$arrow" "$2"
        shift 2
    done
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
    run "Tell Git your name, for every commit on this computer" git config --global user.name "$name"
    run "Tell Git your email, for every commit on this computer" git config --global user.email "$email"
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
            run "Point '$remote' to GitHub's HTTPS address" git remote set-url "$remote" "https://github.com/$repo.git"
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
        if [[ "$(lower "$repo")" == "$(lower "$MAIN_REPO")" && "$remote" == origin ]]; then
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
            "  git pull --rebase origin $(git branch --show-current)" \
            "Conflict? Fix the files the same way as for ifi update, then: git add -A && git rebase --continue"
    fi

    die "Git couldn't reach GitHub. The message above says why. Ask a helper if it's unclear."
}

# Runs a git command that talks to GitHub (fetch, push). Shows it like run,
# and explains the error if it fails. $1 is the remote it talks to, $2 what
# it does.
git_or_explain() {
    local remote="$1" why="$2" err
    shift 2
    step "$why" git "$@"
    GIT_DONE+=("$(shown git "$@")")
    if ! err="$(git "$@" 2>&1)"; then
        explain_git_error "$remote" "$err"
    fi
    git_output "$err"
    return 0
}

# git switch, with a plain explanation when unsaved changes are in the way.
# $1 is what it does.
switch_or_explain() {
    local why="$1" err
    shift
    step "$why" git switch "$@"
    GIT_DONE+=("$(shown git switch "$@")")
    if ! err="$(git switch "$@" 2>&1)"; then
        printf '%s\n\n' "$err" >&2
        if grep -q "would be overwritten" <<<"$err"; then
            echo "Your unsaved changes are in files that are different on the branch you're going to," >&2
            echo "so Git won't switch (it would lose them)." >&2
            if [[ "$(git branch --show-current)" != main ]]; then
                echo "Either save them on this branch first:" >&2
                echo "  ifi save \"Short description of what you changed\"" >&2
                echo "or put them aside, switch, and take them back:" >&2
            else
                echo "Put them aside, switch, and take them back:" >&2
            fi
            die "  git stash        then run the same ifi command again, then:  git stash pop"
        fi
        die "Git couldn't switch branch. The message above says why. Ask a helper if it's unclear."
    fi
    git_output "$err"
}

# Sets $base: the remote that holds the main repo. Collaborators cloned it
# directly (origin). Contributors cloned their fork, so it's upstream, which
# is added here if they skipped that step in get_the_code.md.
find_base() {
    local origin_repo
    origin_repo="$(repo_of origin)"
    if [[ "$(lower "$origin_repo")" == "$(lower "$MAIN_REPO")" ]]; then
        base=origin
    else
        if ! git remote get-url upstream >/dev/null 2>&1; then
            run "Add the main repo as \"upstream\", so Git can get everyone's changes" \
                git remote add upstream "https://github.com/$MAIN_REPO.git"
        fi
        base=upstream
    fi
}

# Fetches the main repo's newest code into $base/main. $1 can say why, when
# it's for something more specific.
fetch_base() {
    git_or_explain "$base" "${1:-Download the newest code from the main repo}" fetch --quiet "$base"
}

git rev-parse --git-dir >/dev/null 2>&1 || die "Run this inside the project folder."
