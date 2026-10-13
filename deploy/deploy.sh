#!/usr/bin/env bash
# Deploys origin/main on the halloween mock server. Run by
# .github/workflows/deploy.yml, or by hand on the server:
#   bash deploy/deploy.sh
#
# Runs in two phases:
#   1. On the old code: pull the new code.
#   2. Re-runs itself from the freshly pulled copy (--after-reset) and does
#      the rest, so edits to this file take effect in the same deploy.
#
# Stripped down from the production script. Left out on purpose, because
# this server holds no data worth keeping and has no visitors to warn:
#   - the 10-minute visitor countdown (announce_deploy)
#   - the pre-migrate database backup (deploy/backup/backup_db.sh)
#   - installing the systemd timers in deploy/systemd/
#   - the DeepL glossary re-sync
#   - the server config drift check (deploy/check_server_config.sh)
# Put the backup back before `migrate` first if that ever stops being true.

set -eo pipefail
cd "$(dirname "$0")/.."   # repo root
source venv/bin/activate

if [ "$1" != "--after-reset" ]; then
    git fetch origin main
    git reset --hard origin/main
    exec bash deploy/deploy.sh --after-reset
fi

pip install -r requirements.txt
cd ifiplatform
python manage.py migrate
python manage.py collectstatic --noinput --clear

sudo systemctl restart gunicorn
python manage.py clear_cache   # after the restart, see clear_cache's docstring

echo "Deploy complete."
