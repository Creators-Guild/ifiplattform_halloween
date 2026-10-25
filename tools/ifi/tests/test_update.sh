# ifi update, ifi update --abort

CARDS=ifiplatform/static/css/cards.css

t_update_when_already_up_to_date() {
    clone_as contributor
    start_issue
    commit "$CARDS" ".event-card { background: orange; }"
    run_ifi update
    succeeds
    has "Already up to date"
}

t_update_puts_your_commits_on_top_of_main() {
    clone_as contributor
    start_issue
    commit "$CARDS" ".event-card { background: orange; }"
    teammate docs/other.md "Other"
    run_ifi update
    succeeds
    has "Updated: bug/orange-cards now has the newest main"
    git merge-base --is-ancestor upstream/main HEAD || fail "main's new commit isn't in the branch"
    same "$(git rev-list --merges --count upstream/main..HEAD)" 0 "merge commits"
    [[ -n "$(git config branch.bug/orange-cards.ifi-before-update)" ]] ||
        fail "should remember where the branch was, for ifi pull-request"
}

t_update_refuses_unsaved_changes() {
    clone_as contributor
    start_issue
    echo "x" >>README.md
    run_ifi update
    fails
    has "Commit your changes first"
}

t_update_refuses_on_main() {
    clone_as contributor
    run_ifi update
    fails
    has "You're on main."
}

t_update_abort_without_an_update() {
    clone_as contributor
    start_issue
    run_ifi update --abort
    fails
    has "No update is running"
}

# Your commit and a teammate's both change the same line of cards.css.
conflict_on_cards() {
    clone_as contributor
    start_issue
    commit "$CARDS" ".event-card { background: orange; }" "Orange cards"
    teammate "$CARDS" ".event-card { background: blue; }"
}

t_update_explains_a_conflict() {
    conflict_on_cards
    run_ifi update
    fails
    has "Conflict! Someone else changed the same lines as you"
    has "This file needs it:"
    has "  $CARDS"
    has "ifi update --abort"
}

t_update_refuses_to_go_on_with_markers_left() {
    conflict_on_cards
    run_ifi update
    run_ifi update
    fails
    has "These files still have conflict markers"
    has "  $CARDS"
}

t_update_goes_on_after_the_conflict_is_fixed() {
    conflict_on_cards
    run_ifi update
    echo ".event-card { background: orange; }" >"$CARDS"
    run_ifi update
    succeeds
    has "Updated:"
    same "$(cat "$CARDS")" ".event-card { background: orange; }" "the fixed file"
    git merge-base --is-ancestor upstream/main HEAD || fail "main's commit isn't in the branch"
}

t_update_leaves_unrelated_new_files_out() {
    conflict_on_cards
    run_ifi update
    echo ".event-card { background: orange; }" >"$CARDS"
    echo "my own notes" >my-notes.txt
    run_ifi update
    succeeds
    git ls-files --error-unmatch my-notes.txt >/dev/null 2>&1 &&
        fail "my-notes.txt was never saved, so the update shouldn't commit it"
    [[ -f my-notes.txt ]] || fail "my-notes.txt should still be there"
}

t_update_abort_puts_the_branch_back() {
    conflict_on_cards
    before="$(git rev-parse HEAD)"
    run_ifi update
    run_ifi update --abort
    succeeds
    has "Back to how your branch was before the update."
    same "$(git rev-parse HEAD)" "$before" "the branch"
    same "$(git status --porcelain)" "" "unsaved changes"
}

# Two commits of yours that touch cards.css, and a teammate's change to it.
two_commits_and_a_conflict() {
    clone_as contributor
    start_issue
    commit "$CARDS" ".event-card { background: orange; }" "Orange cards"
    commit "$CARDS" ".event-card { background: darkorange; }" "Darker orange"
    teammate "$CARDS" ".event-card { background: blue; }"
}

t_update_asks_merge_or_rebase_with_several_commits() {
    two_commits_and_a_conflict
    IN=$'1\nn\n' run_ifi_tty update
    has "How do you want to do that?"
    has "Conflict!"
    git rev-parse --verify --quiet MERGE_HEAD >/dev/null || fail "choosing 1 should start a merge"
    echo ".event-card { background: darkorange; }" >"$CARDS"
    run_ifi update
    succeeds
    same "$(git rev-list --merges --count upstream/main..HEAD)" 1 "merge commits"
}

t_update_rebase_can_stop_once_per_commit() {
    two_commits_and_a_conflict
    IN=$'2\nn\n' run_ifi_tty update
    has "Conflict!"
    # A mix of both, so your next commit (orange -> darkorange) clashes too.
    echo ".event-card { background: purple; }" >"$CARDS"
    run_ifi update
    fails
    has "Another conflict, in your next commit (\"Darker orange\")."
    echo ".event-card { background: darkorange; }" >"$CARDS"
    run_ifi update
    succeeds
    same "$(git rev-list --count upstream/main..HEAD)" 2 "your commits"
}

t_update_shows_the_conflict_how_to() {
    conflict_on_cards
    IN=$'y\n' run_ifi_tty update
    has "Want help fixing it?"
    has "Take one file at a time."
    has "\"Current\" is main's version"
}
