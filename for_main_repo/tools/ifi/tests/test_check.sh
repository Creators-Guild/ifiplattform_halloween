# ifi check, ifi check --quiet

t_check_all_good_for_a_contributor() {
    clone_as contributor
    start_issue
    run_ifi check
    has "✅ origin is your fork: $STUDENT/$NAME"
    has "✅ upstream is the main repo: $MAIN"
    has "✅ Logged in to GitHub, and allowed to push to origin."
    has "Current branch: bug/orange-cards  (issue #5)"
    hasnt "On branch"
    has "✅ No unsaved changes."
    has "✅ Up to date with main in the main repo (upstream/main)."
    hasnt "❌"
}

t_check_for_a_collaborator() {
    clone_as collaborator
    run_ifi check
    has "✅ origin is the main repo ($MAIN): you push straight to it, as a collaborator."
    has "✅ upstream isn't needed"
}

t_check_without_upstream() {
    clone_as contributor no-upstream
    run_ifi check
    fails
    has "❌ No 'upstream' remote"
    has "git remote add upstream https://github.com/$MAIN.git"
}

t_check_with_upstream_pointing_elsewhere() {
    clone_as contributor
    git remote set-url upstream "https://github.com/someone/else.git"
    run_ifi check
    fails
    has "❌ upstream points to someone/else, not the main repo."
}

t_check_with_an_ssh_origin() {
    clone_as contributor
    git remote set-url origin "git@github.com:$STUDENT/$NAME.git"
    run_ifi check
    has "⚠️  origin uses an SSH address"
    has "git remote set-url origin https://github.com/$STUDENT/$NAME.git"
    hasnt "Can't use SSH here"
}

t_check_without_name_and_email() {
    clone_as contributor
    git config --global --unset user.name
    run_ifi check
    fails
    has "❌ Git doesn't know your name and email yet"
}

t_check_on_main() {
    clone_as contributor
    run_ifi check
    has "⚠️  You're on main. Start an issue with: ifi fix-issue <nr>"
}

t_check_on_a_branch_without_an_issue() {
    clone_as contributor
    git switch --quiet -c feature/mine
    run_ifi check
    has "not linked to an issue yet"
}

t_check_counts_unsaved_files() {
    clone_as contributor
    start_issue
    echo "x" >>README.md
    echo "y" >new.txt
    run_ifi check
    has "⚠️  2 file(s) changed but not saved yet"
}

t_check_says_main_moved_on_and_where_it_will_conflict() {
    clone_as contributor
    start_issue
    commit ifiplatform/static/css/cards.css ".event-card { background: orange; }"
    teammate ifiplatform/static/css/cards.css ".event-card { background: blue; }"
    run_ifi check
    has "has 1 new commit(s) since your branch started"
    has "You'll likely get a conflict in: ifiplatform/static/css/cards.css"
}

t_check_says_which_commits_arent_on_github() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi check
    has "⚠️  1 commit(s) aren't on GitHub yet"
    run_ifi pull-request
    commit README.md "Even better readme"
    run_ifi check
    has "⚠️  1 commit(s) aren't on GitHub yet"
    run_ifi pull-request
    run_ifi check
    has "✅ All your commits are on GitHub."
}

t_check_on_a_detached_head() {
    clone_as contributor
    git switch --quiet --detach HEAD
    run_ifi check
    has "You're not on a branch (detached HEAD)."
}

t_check_outside_the_project() {
    mkdir -p "$SANDBOX/elsewhere"
    cd "$SANDBOX/elsewhere" || fail "no folder"
    GIT_CEILING_DIRECTORIES="$SANDBOX" run_ifi check
    fails
    has "You're not in the project folder."
}

t_check_quiet_says_only_ok() {
    clone_as contributor
    start_issue
    run_ifi check --quiet
    succeeds
    same "$OUT" "✅ Setup OK." "the whole output"
}

t_check_quiet_shows_problems_and_main_moving_on() {
    clone_as contributor
    start_issue
    teammate docs/other.md "Other"
    git config --global --unset user.email
    run_ifi check --quiet
    fails
    has "❌ Git doesn't know your name and email yet"
    has "has 1 new commit(s)"
    has "1 problem(s) in your setup."
    hasnt "✅"
}

t_check_with_upstream_that_isnt_on_github() {
    clone_as contributor
    git remote set-url upstream "$SANDBOX/somewhere"
    run_ifi check
    fails
    has "❌ upstream isn't a GitHub address: $SANDBOX/somewhere"
    hasnt "✅ upstream is the main repo"
}

t_check_says_when_your_pull_request_is_merged() {
    clone_as contributor
    start_issue
    commit README.md "Better readme"
    run_ifi pull-request
    merge_pull_request bug/orange-cards
    run_ifi check
    has "🎉 Your pull request for bug/orange-cards is merged into main!"
    hasnt "Update before your pull request"
    has "Your turn:"
    has "Tidy up?"
    has "ifi cleanup   (deletes the branch, takes you to main)"
    has "Want another issue?"
    run_ifi check --quiet
    has "🎉 Your pull request for bug/orange-cards is merged into main!"
    has "Tidy up: ifi cleanup"
}

t_check_your_turn_lists_what_to_do() {
    clone_as contributor
    start_issue
    commit ifiplatform/static/css/cards.css ".event-card { background: orange; }"
    teammate docs/other.md "Other"
    echo "x" >>README.md
    git config --global --unset user.email
    run_ifi check
    has "Your turn:"
    has "Something broken above?"
    has "Changes to keep?"
    has "Want main's new commits?"
    # Problems first, then in the order you'd do them: save, then update.
    same "$(sed -n '/Your turn:/,$p' <<<"$OUT" | grep -o -e "Something broken" -e "Changes to keep" -e "main's new commits" | tr '\n' '|')" \
        "Something broken|Changes to keep|main's new commits|" "the order of the choices"
}

t_check_your_turn_when_all_is_well() {
    clone_as contributor
    start_issue
    run_ifi check
    has "Your turn: carry on with your change."
}

t_check_your_turn_on_main() {
    clone_as contributor
    run_ifi check
    has "Want to start an issue?"
}

t_check_current_branch_on_main_and_detached() {
    clone_as contributor
    run_ifi check
    has "Current branch: main"
    git switch --quiet --detach HEAD
    run_ifi check
    has "Current branch: none (detached HEAD)"
}

t_check_current_branch_is_just_above_your_turn() {
    clone_as contributor
    start_issue
    run_ifi check
    same "$(grep -A2 "Current branch:" <<<"$OUT" | tail -n 1 | cut -c1-10)" "Your turn:" "the line after the branch and a blank line"
}

t_check_problems_are_together_at_the_bottom() {
    clone_as contributor
    start_issue
    git remote remove upstream
    echo "x" >>README.md
    run_ifi check
    # Order: ✅ lines, plain Git, "Needs a look:" with ❌ and ⚠️, branch, "Your turn:".
    same "$(grep -oE '^(✅|Check it yourself|Needs a look:|❌|⚠️|Current branch:|Your turn:)' <<<"$OUT" | uniq | tr '\n' '|')" \
        "✅|Check it yourself|Needs a look:|❌|⚠️|Current branch:|Your turn:|" "the order of the parts"
}

t_check_nothing_needs_a_look() {
    clone_as contributor
    start_issue
    run_ifi check
    has "Nothing needs a look. All good."
    hasnt "Needs a look:"
}

t_check_says_the_commit_identity_is_not_the_login() {
    clone_as contributor
    run_ifi check
    has "✅ Commits are signed as:"
    hasnt "Git knows who you are"
}

t_check_shows_the_github_login_account() {
    clone_as contributor
    git config --global credential.helper '!f() { echo username=octocat; echo password=x; }; f'
    run_ifi check
    has "✅ Logged in to GitHub, and allowed to push to origin. Account: octocat"
}

t_check_accepts_a_username_in_origin() {
    clone_as contributor
    git remote set-url origin "https://octocat@github.com/$STUDENT/$NAME.git"
    run_ifi check
    has "origin is your fork: $STUDENT/$NAME"
    hasnt "origin isn't a GitHub address"
}

t_check_with_gh_selecting_someone_else_than_origin_asks_for() {
    clone_as contributor
    git remote set-url origin "https://octocat@github.com/$STUDENT/$NAME.git"
    git config --global --add credential.https://github.com.helper '!true gh auth git-credential'
    git config --global --add credential.https://github.com.helper '!f() { echo username=hanna; echo password=x; }; f'
    run_ifi check
    has "origin asks for octocat, but your computer's gh has hanna selected"
}
