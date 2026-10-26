# The launchers, ifi help, ifi test's name checks, shell-setup.sh, and that
# the lists of commands agree with each other.

REPO="$(cd "$TOOLS/../.." && pwd)"

# Every command ifi knows, from the case line in tools/ifi/ifi.
known_commands() {
    sed -n 's/^ *fix-issue | \(.*\)) exec.*/fix-issue | \1/p' "$TOOLS/ifi" | tr -d ' ' | tr '|' '\n'
}

t_commands_every_script_parses() {
    local f
    for f in "$TOOLS"/* "$TOOLS"/tests/* "$REPO/ifi"; do
        [[ -f "$f" ]] && head -n 1 "$f" | grep -q bash || continue
        bash -n "$f" || fail "bash can't read $f"
    done
    bash -n "$TOOLS/common.sh" || fail "bash can't read common.sh"
    bash -n "$TOOLS/shell-setup.sh" || fail "bash can't read shell-setup.sh"
}

t_commands_are_executable_in_git() {
    # Without the x bit in Git, a fresh clone (Windows, Mac) can't run them.
    local mode path
    while read -r mode _ _ path; do
        head -n 1 "$REPO/$path" | grep -q '^#!' || continue
        same "$mode" 100755 "the Git mode of $path"
    done < <(cd "$REPO" && git ls-files -s -- tools/ifi ifi)
}

t_commands_lists_agree() {
    local c
    [[ -n "$(known_commands)" ]] || fail "couldn't read the command list in tools/ifi/ifi"
    for c in $(known_commands); do
        [[ -x "$TOOLS/$c" ]] || fail "tools/ifi/ifi knows '$c', but there's no script for it"
        grep -q "^ifi $c" "$TOOLS/pages/ifi.txt" || fail "'ifi help ifi' doesn't list $c"
        grep -q "words=\"help .*\\b$c\\b" "$TOOLS/shell-setup.sh" || fail "Tab completion doesn't know $c"
    done
}

t_commands_unknown_command() {
    clone_as contributor
    run_ifi nope
    fails
    has "ifi: no command called 'nope'. Type: ifi help"
}

t_commands_help_pages() {
    clone_as contributor
    for topic in git docker django ifi; do
        run_ifi help "$topic"
        succeeds
        [[ -n "$OUT" ]] || fail "ifi help $topic is empty"
    done
    run_ifi help nope
    fails
    has "No help page called 'nope'"
    IN=$'4\n' run_ifi help
    has "What do you need help with?"
    has "ifi fix-issue <nr>"
}

t_commands_ifi_cmd_has_windows_line_endings() {
    # cmd.exe misreads a batch file with Unix line endings (.gitattributes).
    same "$(git -C "$REPO" check-attr eol -- ifi.cmd | sed 's/.*: //')" crlf "the eol of ifi.cmd"
    same "$(git -C "$REPO" check-attr eol -- tools/ifi/common.sh | sed 's/.*: //')" lf "the eol of the bash scripts"
}

# ifi test runs Django, so these run in the real repo, not the sandbox.
in_repo_test() {
    cd "$REPO" || fail "no repo"
    run_ifi test "$@"
    grep -q "Can't find a Python with Django" <<<"$OUT" && skip "no Python with Django here"
    return 0
}

t_commands_test_refuses_a_folder() {
    in_repo_test apps.account_app
    fails
    has "is a folder, and Django can't run the tests in a folder here."
    has "ifi test apps.account_app.tests"
}

t_commands_test_refuses_a_misspelled_name() {
    in_repo_test apps.acount_app.tests
    fails
    has "Can't find \"apps.acount_app.tests\". Check the spelling."
}

t_commands_shell_setup_is_quiet_in_scripts() {
    # Sourced from ~/.bashrc by ifi install: scp and rsync break if a
    # non-interactive shell prints anything.
    OUT="$(bash --norc --noprofile -c ". '$TOOLS/shell-setup.sh'" 2>&1)"
    same "$OUT" "" "what a non-interactive shell prints"
}

t_commands_shell_setup_completes_ifi() {
    # The setup check of the first terminal only runs in the container, once.
    OUT="$(bash --norc --noprofile -i -c ". '$TOOLS/shell-setup.sh' >/dev/null 2>&1
        COMP_WORDS=(ifi up); COMP_CWORD=1; _ifi_complete; echo \"[\${COMPREPLY[*]}]\"
        COMP_WORDS=(ifi help d); COMP_CWORD=2; _ifi_complete; echo \"[\${COMPREPLY[*]}]\"" 2>/dev/null)"
    has "[update]"
    has "[docker django]"
}

t_commands_install_adds_ifi_once() {
    [[ -f /.dockerenv ]] && skip "ifi install does nothing inside the container"
    clone_as contributor
    cd "$REPO" || fail "no repo"
    touch "$HOME/.bashrc"
    USE_POSTGRES="" run_ifi install
    succeeds
    has "Added ifi to $HOME/.bashrc."
    grep -qF "alias ifi='$REPO/ifi'" "$HOME/.bashrc" || fail "no alias in .bashrc"
    USE_POSTGRES="" run_ifi install
    has "Already in $HOME/.bashrc."
    same "$(grep -c "alias ifi=" "$HOME/.bashrc")" 1 "aliases in .bashrc"
}



t_commands_prompt_shows_the_branch() {
    clone_as contributor
    start_issue
    OUT="$(bash --norc --noprofile -i -c ". '$TOOLS/shell-setup.sh' >/dev/null 2>&1; echo \"[\${PS1@P}]\"" 2>/dev/null)"
    has "bug/orange-cards"
    cd "$SANDBOX" || fail "no sandbox"
    OUT="$(bash --norc --noprofile -i -c ". '$TOOLS/shell-setup.sh' >/dev/null 2>&1; echo \"[\$(_ifi_branch ' %s')]\"" 2>/dev/null)"
    same "$OUT" "[]" "the branch outside a repo"
}

t_commands_shell_setup_stays_quiet_without_a_terminal() {
    # VS Code starts a hidden interactive shell to read the environment. It
    # mustn't print, or take the first terminal's setup check.
    OUT="$(bash --norc --noprofile -i -c ". '$TOOLS/shell-setup.sh'" </dev/null 2>/dev/null)"
    same "$OUT" "" "what a hidden interactive shell prints"
}

# A new terminal: an interactive bash in a pretend terminal, loading
# shell-setup.sh, with its saved check result in $SANDBOX/state.
new_terminal() {
    command -v script >/dev/null || skip "needs the 'script' command (util-linux)"
    export IFI_STATE_DIR="$SANDBOX/state"
    mkdir -p "$IFI_STATE_DIR"
    PATH="$SANDBOX/bin:$PATH" script -qec "bash --norc --noprofile -i -c '. $TOOLS/shell-setup.sh'" /dev/null </dev/null >"$SANDBOX/terminal.log" 2>&1
    OUT="$(tr -d '\r' <"$SANDBOX/terminal.log" | sed 's/\x1b\[[0-9;]*m//g')"
}

terminal_setup() {
    clone_as contributor
    start_issue
    mkdir -p "$SANDBOX/bin"
    ln -sf "$TOOLS/ifi" "$SANDBOX/bin/ifi"
}

t_commands_first_terminal_checks_and_later_ones_show_the_result() {
    terminal_setup
    new_terminal
    has "Checking your setup..."
    has "✅ Setup OK."
    new_terminal
    hasnt "Checking your setup..."
    has "✅ Setup OK (checked $(date '+%-d %b') "
    has "Check again?  →  ifi check"
}

t_commands_later_terminals_show_the_latest_check() {
    terminal_setup
    new_terminal
    git config --global --unset user.email
    IFI_STATE_DIR="$SANDBOX/state" run_ifi check
    new_terminal
    has "❌ The setup check found 1 problem(s) (checked"
    has "See them?  →  ifi check"
}

t_commands_terminal_while_the_check_is_still_running() {
    terminal_setup
    mkdir -p "$SANDBOX/state"
    : >"$SANDBOX/state/ifi-checked"
    new_terminal
    has "The setup check is still running in another terminal."
    has "See it here?  →  ifi check"
}

t_commands_account_shows_login_and_commit_identity() {
    clone_as contributor
    git config --global credential.helper '!f() { echo username=octocat; echo password=x; }; f'
    run_ifi account
    succeeds
    has "Pushes as:         octocat"
    has "Commits signed as:"
    has "Account picked:    your computer's usual one"
}

# A GitHub profile on the fake API: github_user <login> <id> [name].
github_user() {
    local name=null
    [[ -z "${3:-}" ]] || name="\"$3\""
    mkdir -p "$API_DIR/users"
    printf '{"login": "%s", "id": %s, "name": %s}\n' "$1" "$2" "$name" >"$API_DIR/users/$1"
}

t_commands_account_switch_puts_the_name_in_origin_and_on_commits() {
    github_user octocat 583231 "The Octocat"
    clone_as contributor
    run_ifi account switch octocat
    succeeds
    same "$(git config --get remote.origin.url)" "https://octocat@github.com/$STUDENT/$NAME.git" "origin"
    same "$(git config --local user.name)" "The Octocat" "user.name"
    same "$(git config --local user.email)" "583231+octocat@users.noreply.github.com" "user.email"
    has "Account picked:    octocat"
}

t_commands_account_switch_uses_the_login_when_there_is_no_name() {
    github_user octocat 583231
    clone_as contributor
    run_ifi account switch octocat
    same "$(git config --local user.name)" "octocat" "user.name"
}

t_commands_account_login_asks_for_the_picked_account() {
    github_user octocat 583231
    clone_as contributor
    # Like a login manager with one login per username: hands back the one asked for.
    git config --global credential.helper '!f() { sed -n "s/^username=/username=/p"; echo password=x; }; f'
    run_ifi account switch octocat
    has "Pushes as:         octocat"
}

t_commands_account_switch_without_a_name_goes_back() {
    github_user octocat 583231
    clone_as contributor
    run_ifi account switch octocat
    run_ifi account switch
    succeeds
    same "$(git config --get remote.origin.url)" "https://github.com/$STUDENT/$NAME.git" "origin"
    same "$(git config --local user.email || true)" "" "repo's own user.email"
    has "Back to your computer's usual account"
}

t_commands_account_switch_changes_nothing_when_github_cant_be_reached() {
    github_user offline-cat 1
    clone_as contributor
    git config --global "url.http://127.0.0.1:1/.insteadOf" "https://offline-cat@github.com/"
    run_ifi account switch offline-cat
    fails
    has "Couldn't reach GitHub"
    has "Nothing changed."
    same "$(git config --get remote.origin.url)" "https://github.com/$STUDENT/$NAME.git" "origin"
    same "$(git config --local user.email || true)" "" "repo's own user.email"
}

t_commands_account_switch_to_a_missing_account() {
    clone_as contributor
    run_ifi account switch nobody-here
    fails
    has "GitHub has no account called nobody-here"
    same "$(git config --get remote.origin.url)" "https://github.com/$STUDENT/$NAME.git" "origin"
}

t_commands_account_switch_refuses_ssh() {
    github_user octocat 583231
    clone_as contributor
    git remote set-url origin "git@github.com:$STUDENT/$NAME.git"
    run_ifi account switch octocat
    fails
    has "origin uses SSH"
}

t_commands_account_login_points_to_switch() {
    clone_as contributor
    run_ifi account login
    fails
    has "ifi account login is now: ifi account switch <name>"
}

t_commands_account_refuses_an_unknown_word() {
    clone_as contributor
    run_ifi account nonsense
    fails
    has "ifi account: don't know 'nonsense'"
}

# A computer that logs in with gh, where gh has <account> selected. The gh
# line only has to be there for ifi to see it; the second helper answers.
gh_selected() {
    git config --global --add credential.https://github.com.helper '!true gh auth git-credential'
    git config --global --add credential.https://github.com.helper "!f() { echo username=$1; echo password=x; }; f"
}

t_commands_account_switch_with_gh_selecting_someone_else() {
    github_user octocat 583231
    clone_as contributor
    gh_selected hanna
    run_ifi account switch octocat
    fails
    has "that's hanna. Nothing changed."
    hasnt "Checking that your computer can log in"
    same "$(git config --get remote.origin.url)" "https://github.com/$STUDENT/$NAME.git" "origin"
}

t_commands_account_switch_with_gh_selecting_that_account() {
    github_user octocat 583231
    clone_as contributor
    gh_selected octocat
    run_ifi account switch octocat
    succeeds
    has "✅ Logged in as octocat."
}

t_commands_account_shows_gh_selecting_someone_else() {
    clone_as contributor
    git remote set-url origin "https://octocat@github.com/$STUDENT/$NAME.git"
    gh_selected hanna
    run_ifi account
    has "Your computer's gh has hanna selected, so it gives no login for octocat."
}

t_commands_pull_request_with_gh_selecting_someone_else() {
    clone_as contributor
    start_issue
    commit cards.css "orange"
    git remote set-url origin "https://octocat@github.com/$STUDENT/$NAME.git"
    gh_selected hanna
    run_ifi pull-request
    fails
    has "that's hanna. Nothing changed."
}
