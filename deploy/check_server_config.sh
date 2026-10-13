#!/usr/bin/env bash
# Compares the reference copies in deploy/server_config/ with the live files
# on the server. Prints a GitHub Actions warning (shown on the deploy run's
# summary page) for each file that differs. Never changes anything.
# Run by deploy.sh at the end of every deploy, or by hand:
#   bash deploy/check_server_config.sh

cd "$(dirname "$0")/.."   # repo root
CONFIG=deploy/server_config

check() {
    local copy="$CONFIG/$1" live="$2"
    if [ ! -r "$live" ]; then
        echo "::warning::Server config check: can't read $live (repo copy: $copy)"
        return
    fi
    # The repo copies have the server's IP replaced with <server-ip>, and
    # whitespace differences don't matter in these files.
    local diff_output
    if ! diff_output=$(sed -E 's/\b([0-9]{1,3}\.){3}[0-9]{1,3}\b/<server-ip>/g' "$live" \
            | diff -u -b -B "$copy" -); then
        echo "::warning::Server config drift: $live differs from $copy. Copy the change into the repo, see $CONFIG/README.md"
        echo "$diff_output"
    fi
}

check gunicorn.service    /etc/systemd/system/gunicorn.service
check nginx/ifiplatform   /etc/nginx/sites-available/ifiplatform
check fail2ban/jail.local /etc/fail2ban/jail.local
