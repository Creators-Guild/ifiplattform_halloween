# ifi pull-request

t_pull_request_pushes_to_your_fork_and_gives_the_link() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    succeeds
    has "✓ Sent your branch to your fork on GitHub"
    has "https://github.com/$MAIN/compare/main...$STUDENT:bug/orange-cards?expand=1"
    has "Merged on GitHub?"
    same "$(git ls-remote origin refs/heads/bug/orange-cards | cut -f1)" "$(git rev-parse HEAD)" "the branch on your fork"
    same "$(git rev-parse --abbrev-ref '@{u}')" "origin/bug/orange-cards" "tracks"
}

t_pull_request_link_for_a_collaborator() {
    clone_as collaborator
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    succeeds
    has "https://github.com/$MAIN/compare/main...bug/orange-cards?expand=1"
}

t_pull_request_asks_for_the_issue_when_the_branch_has_none() {
    clone_as contributor
    git switch --quiet -c feature/my-own
    commit README.md "Better readme"
    IN=$'\n#9\n' run_ifi pull-request
    succeeds
    has "write #9 on its \"Closes #\" line"
    same "$(git config branch.feature/my-own.ifi-issue)" 9 "linked issue"
}

t_pull_request_refuses_unsaved_changes() {
    clone_as contributor
    start_issue
    echo "x" >>README.md
    run_ifi pull-request
    fails
    has "These changes aren't committed yet."
}

t_pull_request_refuses_a_branch_without_commits() {
    clone_as contributor
    start_issue
    run_ifi pull-request
    fails
    has "has no commits yet, so there's nothing to send"
}

t_pull_request_after_update_replaces_the_branch_on_github() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    teammate docs/other.md "Other"
    run_ifi update
    run_ifi pull-request
    succeeds
    has "Replaced your branch on GitHub with the updated one."
    same "$(git ls-remote origin refs/heads/bug/orange-cards | cut -f1)" "$(git rev-parse HEAD)" "the branch on your fork"
    [[ -z "$(git config branch.bug/orange-cards.ifi-before-update)" ]] || fail "should forget the old branch tip"
}

t_pull_request_never_overwrites_someone_elses_push() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    # Someone pushes to your branch on GitHub (or presses "Update branch").
    git clone --quiet "https://github.com/$STUDENT/$NAME.git" "$SANDBOX/other"
    (cd "$SANDBOX/other" && git switch --quiet bug/orange-cards && echo "theirs" >theirs.md &&
        git add -A && git commit --quiet -m "Their commit" && git push --quiet origin HEAD)
    theirs="$(git ls-remote origin refs/heads/bug/orange-cards | cut -f1)"
    teammate docs/other.md "Other"
    run_ifi update
    run_ifi pull-request
    fails
    has "Your branch on GitHub has commits that aren't on your computer"
    same "$(git ls-remote origin refs/heads/bug/orange-cards | cut -f1)" "$theirs" "the branch on your fork"
}
