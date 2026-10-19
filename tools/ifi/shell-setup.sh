# Sourced by the dev container's ~/.bashrc (Dockerfile.dev): Tab completion
# for ifi, and a hint in every new terminal.

_ifi_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [[ $COMP_CWORD -eq 1 ]]; then
        mapfile -t COMPREPLY < <(compgen -W "help status fix-issue save pull-request undo-file test migrate restart-server reset-server rebuild-docker" -- "$cur")
    elif [[ $COMP_CWORD -eq 2 && "${COMP_WORDS[1]}" == help ]]; then
        mapfile -t COMPREPLY < <(compgen -W "git docker django ifi" -- "$cur")
    elif [[ $COMP_CWORD -eq 2 && "${COMP_WORDS[1]}" == undo-file ]]; then
        mapfile -t COMPREPLY < <(compgen -W "--extra" -- "$cur")
    fi
}
complete -o default -F _ifi_complete ifi

echo "Stuck? Type: ifi status (what's wrong) or ifi help (cheat sheets)"
