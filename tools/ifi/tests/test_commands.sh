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

t_commands_old_status_name_points_to_check() {
    clone_as contributor
    run_ifi status
    has "ifi status is now called ifi check."
    has "✅ origin is your fork"
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
