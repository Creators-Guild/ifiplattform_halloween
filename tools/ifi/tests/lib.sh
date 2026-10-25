# Shared by tools/ifi/tests/run and playground. Sourced, not run.
#
# A fake GitHub on this computer, so ifi can be tried and tested without
# internet and without touching real GitHub:
#   - Git: url.<local folder>.insteadOf https://github.com/ (and git@github.com:)
#     sends every fetch and push to bare repos in $SANDBOX/remotes/. The
#     remotes still show GitHub addresses, so ifi's fork/collaborator checks
#     run as for real.
#   - The issue API: python's http.server serving JSON files from
#     $API_DIR/repos/<owner>/<repo>/issues/<nr>, through ifi's
#     IFI_GITHUB_API hook. A missing file is a 404, like a missing issue.
#     $API_DIR/users/<name> is an account's profile, for ifi account.
# HOME and GIT_CONFIG_GLOBAL point into the sandbox, so your own
# ~/.gitconfig and ~/.bashrc are never read or changed.

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$(dirname "$TESTS_DIR")"
# Read from common.sh, so the tests keep working when MAIN_REPO changes.
MAIN="$(sed -n 's/^MAIN_REPO="\(.*\)"$/\1/p' "$TOOLS/common.sh")"
NAME="${MAIN#*/}"
STUDENT=student

# Starts the fake issue API on a free port. Sets IFI_GITHUB_API and API_DIR.
start_fake_api() {
    API_DIR="$1"
    mkdir -p "$API_DIR"
    local port
    port="$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
    python3 -m http.server --bind 127.0.0.1 --directory "$API_DIR" "$port" >/dev/null 2>&1 &
    API_PID=$!
    export IFI_GITHUB_API="http://127.0.0.1:$port"
    local i
    for i in $(seq 50); do
        python3 -c "import urllib.request as u; u.urlopen('$IFI_GITHUB_API/')" 2>/dev/null && return
        sleep 0.1
    done
    echo "The fake GitHub API didn't start." >&2
    return 1
}

stop_fake_api() {
    [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null
    return 0
}

# A fresh fake GitHub in $1: the main repo with a few files, a git config of
# its own, and a teammate's clone of main.
new_sandbox() {
    SANDBOX="$1"
    mkdir -p "$SANDBOX/home" "$SANDBOX/remotes"
    export HOME="$SANDBOX/home"
    export GIT_CONFIG_GLOBAL="$HOME/.gitconfig"
    export GIT_CONFIG_NOSYSTEM=1
    export GIT_TERMINAL_PROMPT=0
    export NO_COLOR=1
    git config --global init.defaultBranch main
    git config --global user.name "Student Testesen"
    git config --global user.email "student@example.com"
    git config --global --add "url.file://$SANDBOX/remotes/.insteadOf" "https://github.com/"
    git config --global --add "url.file://$SANDBOX/remotes/.insteadOf" "git@github.com:"
    # The account ifi account switch tests log in as.
    git config --global --add "url.file://$SANDBOX/remotes/.insteadOf" "https://octocat@github.com/"
    git config --global advice.detachedHead false
    rm -rf "${API_DIR:?}/repos" "${API_DIR:?}/users"

    git init --quiet --bare "$SANDBOX/remotes/$MAIN.git"
    git clone --quiet "https://github.com/$MAIN.git" "$SANDBOX/teammate" 2>/dev/null
    (
        cd "$SANDBOX/teammate"
        git config user.name "Teammate"
        git config user.email "teammate@example.com"
        mkdir -p ifiplatform/static/css docs
        echo "# The project" >README.md
        echo ".event-card { background: #222; }" >ifiplatform/static/css/cards.css
        echo "Notes" >docs/notes.md
        git add -A
        git commit --quiet -m "First commit"
        git push --quiet origin main
    )
}

# Your fork on the fake GitHub, as the Fork button makes it.
make_fork() {
    git clone --quiet --bare "$SANDBOX/remotes/$MAIN.git" "$SANDBOX/remotes/$STUDENT/$NAME.git"
}

# Clones into $SANDBOX/work and cd's there. contributor: your fork, with
# upstream (pass no-upstream to skip it). collaborator: the main repo.
clone_as() {
    if [[ "$1" == collaborator ]]; then
        git clone --quiet "https://github.com/$MAIN.git" "$SANDBOX/work"
        cd "$SANDBOX/work" || return 1
    else
        make_fork
        git clone --quiet "https://github.com/$STUDENT/$NAME.git" "$SANDBOX/work"
        cd "$SANDBOX/work" || return 1
        [[ "${2:-}" == no-upstream ]] || git remote add upstream "https://github.com/$MAIN.git"
    fi
}

# Someone else's change, merged into main: teammate <file> <content> [message].
teammate() {
    (
        cd "$SANDBOX/teammate" || exit 1
        git pull --quiet --rebase origin main
        mkdir -p "$(dirname "$1")"
        printf '%s\n' "$2" >"$1"
        git add -A
        git commit --quiet -m "${3:-Teammate changes $1}"
        git push --quiet origin main
    )
}

# Merges your branch (on your fork) into main, like GitHub's merge button:
# merge_pull_request <branch>.
merge_pull_request() {
    (
        cd "$SANDBOX/teammate" || exit 1
        git pull --quiet --rebase origin main
        git fetch --quiet "https://github.com/$STUDENT/$NAME.git" "$1"
        git merge --quiet --no-ff -m "Merge pull request from $STUDENT/$1" FETCH_HEAD
        git push --quiet origin main
    )
}

# An issue on the fake GitHub: issue <nr> <type or ""> <title> [body] [pr].
issue() {
    local dir="$API_DIR/repos/$MAIN/issues"
    mkdir -p "$dir"
    python3 - "$dir/$1" "$2" "$3" "${4:-}" "${5:-}" <<'PY'
import json, sys

path, kind, title, body, pr = sys.argv[1:6]
issue = {"title": title, "body": body, "type": {"name": kind} if kind else None}
if pr:
    issue["pull_request"] = {"url": "https://example.com"}
with open(path, "w", encoding="utf-8") as f:
    json.dump(issue, f)
PY
}

# On the branch for issue 5 ("Orange cards"), as ifi fix-issue makes it.
start_issue() {
    issue 5 Bug "Orange cards"
    "$TOOLS/ifi" fix-issue 5 </dev/null >/dev/null 2>&1 || fail "ifi fix-issue 5 didn't work"
}

# A commit of your own: commit <file> <content> [message].
commit() {
    mkdir -p "$(dirname "$1")"
    printf '%s\n' "$2" >"$1"
    git add -A
    git commit --quiet -m "${3:-Change $1}"
}

# Runs ifi with $IN as what you type (nothing by default). Sets OUT
# (stdout and stderr) and STATUS.
run_ifi() {
    OUT="$(printf '%s' "${IN-}" | "$TOOLS/ifi" "$@" 2>&1)"
    STATUS=$?
}

# Like run_ifi, but in a pretend terminal, for the questions ifi only asks
# when someone can answer. $IN is typed after a moment.
run_ifi_tty() {
    command -v script >/dev/null || skip "needs the 'script' command (util-linux)"
    local cmd log="$SANDBOX/tty.log"
    cmd="$(printf '%q ' "$TOOLS/ifi" "$@")"
    { sleep 1; printf '%s' "${IN-}"; sleep 2; } | script -qec "$cmd" /dev/null >"$log" 2>&1
    STATUS=$?
    OUT="$(tr -d '\r' <"$log")"
}

# The checks. Each stops the test with what went wrong and ifi's output.
fail() {
    echo "FAIL: $*"
    echo "--- output of the last ifi command:"
    printf '%s\n' "${OUT-}"
    exit 1
}
has() { grep -qF -- "$1" <<<"$OUT" || fail "the output should say: $1"; }
hasnt() { ! grep -qF -- "$1" <<<"$OUT" || fail "the output shouldn't say: $1"; }
succeeds() { [[ $STATUS -eq 0 ]] || fail "ifi should succeed, but exited with $STATUS"; }
fails() { [[ $STATUS -ne 0 ]] || fail "ifi should fail, but exited with 0"; }
same() { [[ "$1" == "$2" ]] || fail "${3:-should be the same}: got '$1', expected '$2'"; }
skip() {
    echo "SKIP: $*"
    exit 77
}
