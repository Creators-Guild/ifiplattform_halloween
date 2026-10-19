# Shared by the ifi commands. Sourced, not run.

MAIN_REPO="Creators-Guild/IfiPlatform"

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
        sed -E 's#^(https://github\.com/|git@github\.com:)##; s#\.git$##; s#/$##'
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

git rev-parse --git-dir >/dev/null 2>&1 || die "Run this inside the project folder."
