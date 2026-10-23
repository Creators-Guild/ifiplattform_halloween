# Sourced by the dev container's ~/.bashrc (Dockerfile.dev), and without
# Docker by the line `ifi install` adds to ~/.bashrc: Tab completion for
# ifi, a "(container)" mark in the container's prompt, a hint in every
# new terminal, and a setup check in the first one. Works in bash 3.2 too (a Mac), so no mapfile.

_ifi_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}" words=""
    if [[ $COMP_CWORD -eq 1 ]]; then
        words="help status fix-issue save update pull-request undo-file cleanup test migrate restart-server reset-server rebuild-docker install"
    elif [[ $COMP_CWORD -eq 2 && "${COMP_WORDS[1]}" == help ]]; then
        words="git docker django ifi"
    elif [[ $COMP_CWORD -eq 2 && "${COMP_WORDS[1]}" == undo-file ]]; then
        words="--extra"
    elif [[ $COMP_CWORD -eq 2 && "${COMP_WORDS[1]}" == update ]]; then
        words="--abort"
    fi
    COMPREPLY=($(compgen -W "$words" -- "$cur"))
}
complete -o default -F _ifi_complete ifi

# Shows where a terminal runs: inside the container, ifi and the site's
# Python are there; on your own computer, your GitHub login is.
if [[ -f /.dockerenv ]]; then
    PS1='\[\e[1;35m\](container)\[\e[0m\] \w \$ '
fi

echo "Stuck? Type: ifi status (what's wrong) or ifi help (cheat sheets)"

# The first terminal after the container starts also checks the setup and
# shows only what's broken. /dev/shm is emptied every time the container
# starts, and noclobber lets only one terminal create the file when VS Code
# opens several at once.
if [[ -f /.dockerenv ]] && (set -o noclobber; : >/dev/shm/ifi-status-checked) 2>/dev/null; then
    echo "Checking your setup..."
    ifi status --quiet
fi
