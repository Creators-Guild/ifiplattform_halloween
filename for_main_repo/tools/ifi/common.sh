# Shared by the ifi commands. Sourced, not run.

MAIN_REPO="Creators-Guild/IfiPlatform"

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
    C_BOLD=$'\e[1m' C_CMD=$'\e[36m' C_DIM=$'\e[2m' C_OK=$'\e[32m' C_BAD=$'\e[31m' C_OFF=$'\e[0m'
else
    C_BOLD="" C_CMD="" C_DIM="" C_OK="" C_BAD="" C_OFF=""
fi

# Every command ifi runs is listed under "Done for you:" as a ✓ line (✗ when
# it failed) with the command under it, so people see what ifi did, and the
# real Git behind it to type themselves later. Then "Your turn:" says what's
# up to them. GIT_DONE collects the git commands for git_recap.
STEPS_SHOWN=false
GIT_DONE=()

# A step's text is an order ("Download the newest code"). verb_form makes
# the other forms of it: past ("Downloaded the newest code"), ing
# ("Downloading ...") or couldnt ("Couldn't download ..."). Fails for a verb
# that isn't in the list (tests/test_output.sh checks every step's verb).
verb_form() {
    local form="$1" text="$2" verb rest past ing
    verb="${text%% *}"
    rest="${text#"$verb"}"
    case "$verb" in
        Add) past=Added ing=Adding ;;
        Apply) past=Applied ing=Applying ;;
        Bring) past=Brought ing=Bringing ;;
        Commit) past=Committed ing=Committing ;;
        Delete) past=Deleted ing=Deleting ;;
        Download) past=Downloaded ing=Downloading ;;
        Empty) past=Emptied ing=Emptying ;;
        Fill) past=Filled ing=Filling ;;
        Finish) past=Finished ing=Finishing ;;
        Go) past=Went ing=Going ;;
        Keep) past=Kept ing=Keeping ;;
        Make) past=Made ing=Making ;;
        Mark) past=Marked ing=Marking ;;
        Move) past=Moved ing=Moving ;;
        Point) past=Pointed ing=Pointing ;;
        Put) past=Put ing=Putting ;;
        Rename) past=Renamed ing=Renaming ;;
        Replace) past=Replaced ing=Replacing ;;
        Run) past=Ran ing=Running ;;
        Send) past=Sent ing=Sending ;;
        Stop) past=Stopped ing=Stopping ;;
        Switch) past=Switched ing=Switching ;;
        Take) past=Took ing=Taking ;;
        Tell) past=Told ing=Telling ;;
        *)
            printf '%s' "$text"
            return 1
            ;;
    esac
    case "$form" in
        past) printf '%s%s' "$past" "$rest" ;;
        ing) printf '%s%s' "$ing" "$rest" ;;
        couldnt) printf "Couldn't %s%s" "$(lower "$verb")" "$rest" ;;
    esac
}

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

# "Done for you:", once, above the first step.
steps_heading() {
    $STEPS_SHOWN && return 0
    STEPS_SHOWN=true
    printf '\n%sDone for you:%s\n' "$C_BOLD" "$C_OFF"
}

# The command under a step. --quiet only keeps ifi's own output short, so
# it isn't shown (nor in git_recap).
step_command() {
    printf '      %s$ %s%s\n' "$C_CMD" "$(shown "$@" | sed 's/ --quiet//g')" "$C_OFF"
}

# While a step runs, in a terminal: a dim "⋯ Downloading ..." line, so a
# slow fetch doesn't look frozen. step_done writes over it.
step_start() {
    steps_heading
    [[ -t 1 ]] && printf '  %s⋯ %s …%s' "$C_DIM" "$(verb_form ing "$1")" "$C_OFF"
    return 0
}

# step_done ok|fail "what it does" [command...]: the ✓ or ✗ line, and the
# command under it.
step_done() {
    local result="$1" why="$2"
    shift 2
    [[ -t 1 ]] && printf '\r\e[K'
    if [[ "$result" == ok ]]; then
        printf '  %s✓%s %s\n' "$C_OK" "$C_OFF" "$(verb_form past "$why")"
    else
        printf '  %s✗%s %s\n' "$C_BAD" "$C_OFF" "$(verb_form couldnt "$why")"
    fi
    [[ $# -eq 0 ]] || step_command "$@"
}

# Git's own output, under a label so it's clear Git is talking, not ifi.
# Only shown when a step failed: the ✓ line says it all otherwise. Git's
# "hint:" lines are left out: ifi says what to do next itself, and the
# hints suggest other things (git rebase --skip, git pull).
git_output() {
    local out
    out="$(grep -v '^hint:' <<<"$1")"
    [[ -n "$out" ]] || return 0
    printf '      %sGit output:%s\n' "$C_DIM" "$C_OFF"
    printf '%s\n' "$out" | sed 's/^/        /'
}

# run "what it does" command...: runs it as a step. Other commands than git
# (Django) print straight through, between the "▸" line and the ✓, since
# makemigrations can ask questions and the tests print a lot. A leading
# `env VAR=x` is run but not shown.
run() {
    local why="$1"
    shift
    local cmd=("$@") out status=0
    if [[ "$1" == env ]]; then
        cmd=("${@:2}")
        while [[ "${cmd[0]}" == *=* ]]; do cmd=("${cmd[@]:1}"); done
    fi
    if [[ "${cmd[0]}" != git ]]; then
        steps_heading
        printf '  %s▸ %s%s\n' "$C_BOLD" "$(verb_form ing "$why")" "$C_OFF"
        step_command "${cmd[@]}"
        "$@" || status=$?
        if [[ $status -eq 0 ]]; then step_done ok "$why"; else step_done fail "$why"; fi
        return $status
    fi
    GIT_DONE+=("$(shown "${cmd[@]}")")
    step_start "$why"
    out="$("$@" 2>&1)" || status=$?
    if [[ $status -eq 0 ]]; then
        step_done ok "$why" "${cmd[@]}"
    else
        step_done fail "$why" "${cmd[@]}"
        git_output "$out"
    fi
    return $status
}

# "In plain Git, this was:" with every git command this run used.
git_recap() {
    [[ ${#GIT_DONE[@]} -gt 0 ]] || return 0
    echo
    echo "In plain Git, this was:"
    printf '  %s\n' "${GIT_DONE[@]}" | sed 's/ --quiet//g'
}

# "Your turn:" and what's up to you now, before the choices.
your_turn() {
    printf '\n%sYour turn:%s%s\n' "$C_BOLD" "$C_OFF" "${1:+ $1}"
}

# The choices after "Your turn:": pairs of situation and what to do, arrows lined up.
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

# "owner/repo" from a GitHub remote: https (also https://name@github.com/) or ssh.
repo_of() {
    git config --get "remote.$1.url" |
        sed -E 's#^(https://([^@/]+@)?github\.com/|ssh://git@github\.com/|git@github\.com:)##; s#\.git$##; s#/$##'
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
# behind or other. Shared by explain_git_error and `ifi check`.
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

# The GitHub account Git logs in with when it pushes: the username its
# credential helper hands out. Empty if there is none, or it takes too long.
# This is the login, not the name and email on commits (git config user.name).
# Asks with origin's address, so ifi account's username counts, or with $1.
github_login() {
    local url="${1:-$(git config --get remote.origin.url 2>/dev/null || true)}"
    if [[ "$url" == https://* ]]; then
        printf 'url=%s\n\n' "$url"
    else
        printf 'protocol=https\nhost=github.com\n\n'
    fi |
        GIT_TERMINAL_PROMPT=0 with_timeout 5 git credential fill 2>/dev/null |
        sed -n 's/^username=//p' | head -n 1 || true
}

# The username in origin's address (ifi account switch), empty if none.
picked_account() {
    git config --get remote.origin.url 2>/dev/null | sed -nE 's#^https://([^@/]+)@github\.com/.*#\1#p'
}

# When the computer logs in with gh and gh has another account than $1
# selected: prints that account. Asking for $1 would then pop up a password
# window on the computer, so callers skip it. Asking without a name doesn't.
gh_selects_other() {
    [[ "$(login_tool)" == gh ]] || return 1
    local selected
    selected="$(github_login https://github.com)"
    [[ -n "$selected" && "$(lower "$selected")" != "$(lower "$1")" ]] || return 1
    echo "$selected"
}

# Which tool hands out GitHub logins: gh, gcm, keychain or unknown. In the
# container this reads the computer's ~/.gitconfig, which VS Code copies in.
login_tool() {
    local helpers
    helpers="$({ git config --get-all credential.https://github.com.helper; git config --get-all credential.helper; } 2>/dev/null || true)"
    case "$helpers" in
        *"gh auth git-credential"*) echo gh ;;
        *manager*) echo gcm ;;
        *osxkeychain*) echo keychain ;;
        *) echo unknown ;;
    esac
}

# Why the computer gave no login for account $1, and what to do, for the
# tool it uses. $2: gh's selected account, if known. Always exits. Background: docs/claude_context/ifi_account.md
explain_account_login() {
    local name="$1" where="in this terminal"
    in_container && where="on your computer, not in the container"
    {
        case "$(login_tool)" in
            gh)
                echo "Your computer logs in to GitHub with the GitHub CLI (gh). gh only hands out"
                echo "the account that's selected in it, and that's ${2:-not $name}. Nothing changed."
                echo "gh's selected account counts for all your repos. Switch back with: gh auth switch"
                your_turn
                choices \
                    "Push as $name?" "run these $where:" \
                    "" "  gh auth login               (only the first time: log in as $name)" \
                    "" "  gh auth switch --user $name" \
                    "" "then here: ifi account switch $name" \
                    "Keep your usual account?" "nothing to do"
                ;;
            gcm)
                echo "The login window was closed, or you logged in as another account. Nothing changed."
                your_turn
                choices \
                    "Push as $name?" "ifi account switch $name, and log in as $name in the window" \
                    "Keep your usual account?" "nothing to do"
                ;;
            *)
                echo "Your computer has no saved login for $name, and nothing that opens a login"
                echo "window for it. Nothing changed."
                your_turn
                choices \
                    "On Windows?" "update Git for Windows (git-scm.com). It has the login window." \
                    "On a Mac or Linux?" "install the GitHub CLI (cli.github.com), then $where:" \
                    "" "  gh auth login               (log in as $name, answer Yes to \"Authenticate Git\")" \
                    "" "  gh auth switch --user $name" \
                    "Then" "ifi account switch $name" \
                    "Keep your usual account?" "nothing to do" \
                    "More help?" "docs/contributing/docker_guide.md#another-github-account-in-the-container"
                ;;
        esac
    } >&2
    exit 1
}

# Explains a failed fetch or push in plain words. $1 is the remote, $2 is
# what Git printed (git_or_explain has shown it already). Always exits.
explain_git_error() {
    local remote="$1" err="$2" url repo kind
    url="$(git config --get "remote.$remote.url" || true)"
    repo="$(repo_of "$remote")"
    kind="$(git_error_kind "$err")"
    echo >&2

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
            "Or push as another account: ifi account switch <name>" \
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
    local picked other=""
    picked="$(picked_account)"
    if [[ "$remote" == origin && "$1" == push && -n "$picked" ]] && other="$(gh_selects_other "$picked")"; then
        explain_account_login "$picked" "$other"
    fi
    GIT_DONE+=("$(shown git "$@")")
    step_start "$why"
    if ! err="$(git "$@" 2>&1)"; then
        step_done fail "$why" git "$@"
        git_output "$err"
        explain_git_error "$remote" "$err"
    fi
    step_done ok "$why" git "$@"
}

# Pushes the current branch to origin; $1 is what it does. After `ifi
# update` the branch has new commits in place of the old ones, so GitHub
# refuses a normal push. Then it replaces the branch on GitHub, but only if
# it still has nothing but what was there before the update (a lease on that
# exact commit), so nobody else's work is ever overwritten.
push_branch() {
    local why="$1" branch before remote_tip=""
    branch="$(git branch --show-current)"
    before="$(git config "branch.$branch.ifi-before-update" || true)"
    [[ -n "$before" ]] && remote_tip="$(GIT_TERMINAL_PROMPT=0 git ls-remote origin "refs/heads/$branch" 2>/dev/null | cut -f1 || true)"
    if [[ -n "$remote_tip" ]] && ! git merge-base --is-ancestor "$remote_tip" HEAD 2>/dev/null &&
        git merge-base --is-ancestor "$remote_tip" "$before" 2>/dev/null; then
        git_or_explain origin "Replace your branch on GitHub with the updated one. Git refuses if someone else pushed to it in the meantime, so nothing gets lost" \
            push --quiet -u --force-with-lease="refs/heads/$branch:$remote_tip" origin HEAD
    else
        git_or_explain origin "$why" push --quiet -u origin HEAD
    fi
    git config --unset "branch.$branch.ifi-before-update" || true
}

# git switch, with a plain explanation when unsaved changes are in the way.
# $1 is what it does.
switch_or_explain() {
    local why="$1" err
    shift
    GIT_DONE+=("$(shown git switch "$@")")
    step_start "$why"
    if ! err="$(git switch "$@" 2>&1)"; then
        step_done fail "$why" git switch "$@"
        git_output "$err"
        echo >&2
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
    step_done ok "$why" git switch "$@"
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

# True when $1 (a branch or commit) is merged into $base/main: all its
# commits are in main, and it isn't simply one of main's own commits (a
# branch just made by ifi fix-issue, with no commits yet). Merged pull
# requests sit beside main's own line of commits, joined by a merge commit.
merged_into_main() {
    git merge-base --is-ancestor "$1" "$base/main" 2>/dev/null &&
        ! git rev-list --first-parent "$base/main" | grep -qxF "$(git rev-parse "$1")"
}

# Fetches the main repo's newest code into $base/main. $1 can say why, when
# it's for something more specific.
fetch_base() {
    git_or_explain "$base" "${1:-Download the newest code from the main repo}" fetch --quiet "$base"
}

git rev-parse --git-dir >/dev/null 2>&1 || die "Run this inside the project folder."
