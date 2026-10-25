# How ifi shows what it did: "Done for you:" with ✓ or ✗ lines and the
# commands, then "Your turn:" (the step helpers in common.sh).

# Runs common.sh's helpers in the sandbox clone: helpers 'run "..." true'.
helpers() {
    OUT="$(bash -c 'source "$1/common.sh"; eval "$2"' _ "$TOOLS" "$1" 2>&1)"
    STATUS=$?
}

t_output_lists_what_was_done_then_your_turn() {
    clone_as contributor
    issue 5 Bug "Orange cards"
    run_ifi fix-issue 5
    succeeds
    has "Done for you:"
    has "  ✓ Downloaded the newest code from the main repo"
    has "      \$ git fetch upstream"
    has "  ✓ Made the branch bug/orange-cards from the newest main"
    has "(switch -c makes the branch and moves you onto it: you are on bug/orange-cards now)"
    has "Your turn: make your change."
    hasnt "Git output:"
    [[ "$(grep -c "Done for you:" <<<"$OUT")" -eq 1 ]] || fail "\"Done for you:\" should be there once"
}

t_output_shows_a_failed_step_with_gits_words() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    git remote set-url origin "https://github.com/nobody/$NAME.git"
    run_ifi pull-request
    fails
    has "  ✗ Couldn't send your branch to your fork on GitHub"
    has "      Git output:"
    hasnt "✓ Sent your branch"
}

t_output_every_step_has_known_verbs() {
    clone_as contributor
    local texts text
    # The texts given to run, git_or_explain, ...: the same calls the step
    # helpers make, so a new step with a verb verb_form doesn't know fails here.
    texts="$(cd "$TOOLS" && grep -hoE '(\brun|git_or_explain [^ ]+|switch_or_explain|push_branch|fetch_base|step_start|step_done (ok|fail)) "[A-Z][^"]*|why="[A-Z][^"]*|\$\{1:-[A-Z][^}]*' -- * |
        sed -E 's/.*"//; s/^\$\{1:-//')"
    [[ -n "$texts" ]] || fail "found no step texts"
    while IFS= read -r text; do
        [[ "$text" == \$* ]] && continue
        helpers "verb_form past \"$text\" >/dev/null" || fail "verb_form doesn't know the first word of: $text"
    done <<<"$texts"
}

t_output_other_commands_print_between_the_lines() {
    clone_as contributor
    helpers 'run "Run a small check" echo "hello from the check"'
    succeeds
    has "  ▸ Running a small check"
    has "      \$ echo \"hello from the check\""
    has "hello from the check"
    has "  ✓ Ran a small check"
    helpers 'run "Run a small check" false'
    fails
    has "  ✗ Couldn't run a small check"
}

t_output_shows_progress_in_a_terminal() {
    clone_as contributor
    issue 5 Bug "Orange cards"
    run_ifi_tty fix-issue 5
    has "⋯ Downloading the newest code from the main repo"
    has "✓ Downloaded the newest code from the main repo"
    grep -q $'\e\\[K' "$SANDBOX/tty.log" || fail "the progress line should be written over"
}

t_output_leaves_out_gits_hints() {
    clone_as contributor
    start_issue
    commit ifiplatform/static/css/cards.css ".event-card { background: orange; }"
    teammate ifiplatform/static/css/cards.css ".event-card { background: blue; }"
    run_ifi update
    has "CONFLICT (content)"
    hasnt "hint:"
    hasnt "git rebase --skip"
}
