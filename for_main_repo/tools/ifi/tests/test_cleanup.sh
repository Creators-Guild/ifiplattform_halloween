# ifi cleanup

# Your issue-5 branch, sent as a pull request and merged by a teammate.
merged_issue_branch() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    merge_pull_request bug/orange-cards
    git switch --quiet main
}

t_cleanup_deletes_merged_branches_here_and_on_your_fork() {
    merged_issue_branch
    IN=$'y\n' run_ifi cleanup
    succeeds
    has "These branches are merged into main"
    has "Your fork on GitHub has them too"
    git show-ref --verify --quiet refs/heads/bug/orange-cards && fail "should be deleted on your computer"
    [[ -z "$(git ls-remote origin refs/heads/bug/orange-cards)" ]] || fail "should be deleted on your fork"
}

t_cleanup_asks_first() {
    merged_issue_branch
    IN=$'n\n' run_ifi cleanup
    fails
    has "Nothing was deleted."
    git show-ref --verify --quiet refs/heads/bug/orange-cards || fail "should still be there"
}

t_cleanup_keeps_branches_that_arent_merged() {
    merged_issue_branch
    issue 6 Bug "Blue cards"
    run_ifi fix-issue 6
    commit docs/notes.md "Blue"
    git switch --quiet main
    IN=$'y\n' run_ifi cleanup
    succeeds
    git show-ref --verify --quiet refs/heads/bug/blue-cards || fail "bug/blue-cards isn't merged, so it should stay"
}

t_cleanup_keeps_a_new_branch_without_commits() {
    merged_issue_branch
    issue 6 Bug "Blue cards"
    run_ifi update
    run_ifi fix-issue 6
    git switch --quiet main
    IN=$'y\n' run_ifi cleanup
    hasnt "bug/blue-cards"
    git show-ref --verify --quiet refs/heads/bug/blue-cards ||
        fail "bug/blue-cards was just made and has no work yet, so it should stay"
}

t_cleanup_lists_backups_on_their_own() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    commit docs/notes.md "Oops"
    run_ifi undo-file docs/notes.md
    merge_pull_request bug/orange-cards
    git switch --quiet main
    IN=$'n\n' run_ifi cleanup
    has "And these backups from ifi undo-file"
}

t_cleanup_with_nothing_to_clean() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi cleanup
    succeeds
    has "Nothing to clean up"
}

t_cleanup_switches_you_off_a_merged_branch() {
    merged_issue_branch
    git switch --quiet bug/orange-cards
    IN=$'y\n' run_ifi cleanup
    succeeds
    has "bug/orange-cards   (you're on it, so ifi switches you to main first)"
    has "✓ Switched to main, since bug/orange-cards is merged"
    has "Want another issue?"
    same "$(git branch --show-current)" main "branch"
    git show-ref --verify --quiet refs/heads/bug/orange-cards && fail "bug/orange-cards should be deleted"
    return 0
}

t_cleanup_keeps_a_merged_branch_with_unsaved_changes() {
    merged_issue_branch
    git switch --quiet bug/orange-cards
    echo "new work" >>docs/notes.md
    IN=$'y\n' run_ifi cleanup
    succeeds
    has "Nothing to clean up"
    has "bug/orange-cards is merged too, but it has changes that aren't saved"
    same "$(git branch --show-current)" bug/orange-cards "branch"
}

t_cleanup_makes_main_again_when_it_is_gone() {
    merged_issue_branch
    git switch --quiet bug/orange-cards
    git branch --quiet -D main
    IN=$'y\n' run_ifi cleanup
    succeeds
    has "✓ Switched to a new main"
    same "$(git branch --show-current)" main "branch"
    same "$(git rev-parse HEAD)" "$(git rev-parse upstream/main)" "main"
}

t_cleanup_doesnt_call_a_new_branch_merged() {
    clone_as contributor
    start_issue
    run_ifi cleanup
    succeeds
    hasnt "which is merged"
}
