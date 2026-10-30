#!/usr/bin/env bash
# Deletes the Halloween mock site's data, as its privacy notice promises
# ("deleted no later than 2 November 2026"). Run as root by
# halloween-wipe.timer, or by hand from anywhere:
#   sudo bash deploy/halloween/wipe_mock_site.sh --dry-run   # only lists
#   sudo bash deploy/halloween/wipe_mock_site.sh
# If --dry-run exits non-zero, fix that before installing the timer.
# Plan: docs/claude_plans/halloween_mock_site_totals.md.
#
# Keeps going if a step fails and exits non-zero at the end if any did.
# Every step is safe to repeat, so after a failure just run it again: the
# done file is only written once every step has succeeded. Logs only what
# it removed, never any content (journalctl -u halloween-wipe).

set -uo pipefail
cd "$(dirname "$0")/../.."   # repo root

# Overridable only so the script can be tried against fake folders.
BACKUP_ROOT=${WIPE_BACKUP_ROOT:-/mnt/backups}
STATE_DIR=${WIPE_STATE_DIR:-/var/lib/halloween-wipe}
TIMERS=(ifiplatform-backup sync-peoply-events ifiplatform-translate ifiplatform-translate-nightly)
export COMPOSE_FILE=compose.prod.yml

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true
FAILED=0

log() { echo "$(date -Is) $*"; }
fail() { log "FAILED: $*" >&2; FAILED=1; }

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this as root (sudo)." >&2
    exit 1
fi
if [ -f "$STATE_DIR/done" ]; then
    log "Already wiped at $(cat "$STATE_DIR/done"). Nothing to do."
    exit 0
fi
$DRY_RUN && log "Dry run: nothing is deleted."

log "== 1. Timers"
for timer in "${TIMERS[@]}"; do
    if ! systemctl cat "$timer.timer" >/dev/null 2>&1; then
        log "$timer.timer: not installed"
    elif $DRY_RUN; then
        log "$timer.timer: would stop and disable"
    elif systemctl disable --now "$timer.timer" && systemctl stop "$timer.service"; then
        log "$timer.timer: stopped and disabled"
    else
        fail "stopping $timer.timer"
    fi
done

log "== 2. Containers and volumes"
project=$(docker compose config 2>/dev/null | sed -n 's/^name: //p' | head -n 1)
if [ -z "$project" ]; then
    fail "docker compose config (is Docker running, is $COMPOSE_FILE here?)"
else
    containers=$(docker ps -aq --filter "label=com.docker.compose.project=$project" | wc -l)
    volumes=$(docker volume ls -q --filter "label=com.docker.compose.project=$project" | paste -sd ' ')
    log "project $project: $containers container(s), volumes: ${volumes:-none}"
    if $DRY_RUN; then
        log "would run: docker compose down -v --remove-orphans"
    elif docker compose down -v --remove-orphans; then
        log "removed $containers container(s) and their logs, and volumes: ${volumes:-none}"
    else
        fail "docker compose down -v"
        fi
fi

log "== 3. Backups"
for dir in "$BACKUP_ROOT/postgres" "$BACKUP_ROOT/media"; do
    if [ ! -d "$dir" ]; then
        log "$dir: doesn't exist"
        continue
    fi
    files=$(find "$dir" -type f | wc -l)
    if $DRY_RUN; then
        log "$dir: would delete $files backup file(s)"
    elif find "$dir" -mindepth 1 -delete; then
        log "$dir: deleted $files backup file(s)"
    else
        fail "deleting in $dir"
    fi
done

log "== 4. .env files"
for env_file in .env ifiplatform/.env; do
    if [ "$FAILED" -ne 0 ] && ! $DRY_RUN; then
        # Compose needs .env, so a rerun needs it too.
        log "$env_file: kept until the steps above have worked"
    elif [ ! -e "$env_file" ]; then
        log "$env_file: doesn't exist"
    elif $DRY_RUN; then
        log "$env_file: would delete"
    elif rm -f "$env_file"; then
        log "$env_file: deleted"
    else
        fail "deleting $env_file"
    fi
done

if [ "$FAILED" -ne 0 ]; then
    log "Some steps failed (see above). Fix them, then run this again."
    exit 1
fi
if $DRY_RUN; then
    log "Dry run OK."
    exit 0
fi
mkdir -p "$STATE_DIR"
date -Is > "$STATE_DIR/done"
log "Wipe complete."
