# Sourced by the dev container's ~/.bashrc (Dockerfile.dev), and without
# Docker by the line `ifi install` adds to ~/.bashrc: Tab completion for
# ifi, a "(container)" mark in the container's prompt, a hint in every
# new terminal, and a setup check in the first one. Works in bash 3.2 too (a Mac), so no mapfile.

# Only for terminals you type in: scp, rsync and scripts break when a
# non-interactive shell prints anything, and some ~/.bashrc files don't stop
# those before the line that loads this.
[[ $- == *i* ]] || return 0

_ifi_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}" words=""
    if [[ $COMP_CWORD -eq 1 ]]; then
        words="help check fix-issue save update pull-request undo-file cleanup test migrate restart-server wipe-database rebuild-docker install"
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

# The branch you're on, for the prompt: "$1" with %s as the name, like
# printf. Nothing outside a repo or on a detached HEAD.
_ifi_branch() {
    local b
    b="$(git branch --show-current 2>/dev/null)" || return 0
    [[ -n "$b" ]] && printf "$1" "$b"
    return 0
}

# The prompt shows where a terminal runs (inside the container, ifi and the
# site's Python are there; on your own computer, your GitHub login is) and
# the branch you're on, so you notice before you commit to the wrong one:
#   (container) bug/orange-cards ~/ifiplatform $
# On your own computer the branch goes in front of your own prompt, unless
# it already shows one (Git Bash's does).
if [[ -f /.dockerenv ]]; then
    PS1='\[\e[1;35m\](container)\[\e[0m\]\[\e[1;33m\]$(_ifi_branch " %s")\[\e[0m\] \w \$ '
elif [[ "$PS1" != *__git_ps1* && "$PS1" != *_ifi_branch* ]]; then
    PS1='\[\e[1;33m\]$(_ifi_branch "(%s) ")\[\e[0m\]'"$PS1"
fi

# The rest only in a terminal you can see. VS Code also starts a hidden
# shell when it connects to the container, to read the environment: it
# would take the setup check below, and nobody would see it.
[[ -t 0 && -t 1 ]] || return 0

echo "Stuck? Type: ifi check (what's wrong) or ifi help (cheat sheets)"

# The first terminal after the container starts also checks the setup and
# shows only what's broken. /dev/shm is emptied every time the container
# starts, and noclobber lets only one terminal create the file when VS Code
# opens several at once.
if [[ -f /.dockerenv ]] && (set -o noclobber; : >/dev/shm/ifi-checked) 2>/dev/null; then
    echo "Checking your setup..."
    ifi check --quiet
fi
