# ifi save "message"

t_save_commits_changes_in_every_folder() {
    clone_as contributor
    start_issue
    echo "More notes" >>docs/notes.md
    mkdir -p tools && echo "echo hi" >tools/new.sh
    cd ifiplatform
    run_ifi save "Add notes and a tool"
    succeeds
    has "changed  docs/notes.md"
    has "new      tools/new.sh"
    same "$(git status --porcelain)" "" "unsaved changes"
    same "$(git log -1 --format=%s)" "Add notes and a tool" "commit message"
}

t_save_asks_for_a_message() {
    clone_as contributor
    start_issue
    echo "More" >>README.md
    IN=$'   \nUpdate the readme\n' run_ifi save
    succeeds
    same "$(git log -1 --format=%s)" "Update the readme" "commit message"
}

t_save_asks_for_name_and_email_the_first_time() {
    clone_as contributor
    start_issue
    git config --global --unset user.name
    git config --global --unset user.email
    echo "More" >>README.md
    IN=$'Kari Nordmann\nnot-an-email\nkari@example.com\n' run_ifi save "Update the readme"
    succeeds
    has "Git needs your name and email once."
    same "$(git config --global user.name)" "Kari Nordmann" "name"
    same "$(git log -1 --format='%an <%ae>')" "Kari Nordmann <kari@example.com>" "author"
}

t_save_refuses_on_main() {
    clone_as contributor
    echo "More" >>README.md
    run_ifi save "Update the readme"
    fails
    has "You're on main."
}

t_save_with_nothing_to_save() {
    clone_as contributor
    start_issue
    run_ifi save "Nothing"
    fails
    has "Nothing to commit"
}
