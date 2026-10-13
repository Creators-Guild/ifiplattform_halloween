#!/usr/bin/env bash
# Deploys origin/main on the server. Run by .github/workflows/deploy.yml,
# or by hand on the server if GitHub Actions is unavailable:
#   bash deploy/deploy.sh
#   SKIP_COUNTDOWN=true bash deploy/deploy.sh   # skip the 10-minute visitor warning
#
# Runs in two phases:
#   1. On the old code: warn visitors, then pull the new code.
#   2. Re-runs itself from the freshly pulled copy (--after-reset) and does
#      the rest, so edits to this file take effect in the same deploy.

set -eo pipefail
cd "$(dirname "$0")/.."   # repo root
source venv/bin/activate

if [ "$1" != "--after-reset" ]; then
    # Countdown before the reset: the running site keeps serving the old
    # code (and shows the banner) while we wait.
    if [ "$SKIP_COUNTDOWN" != "true" ]; then
        (cd ifiplatform && python manage.py announce_deploy --minutes 10)
        echo "Waiting 10 minutes for the visitor warning..."
        sleep 600
    fi
    OLD_SHA=$(git rev-parse HEAD)
    git fetch origin main
    git reset --hard origin/main
    exec bash deploy/deploy.sh --after-reset "$OLD_SHA"
fi
OLD_SHA=$2

# systemd reads its own copy of these files, not the repo's.
sudo cp deploy/systemd/*.service deploy/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
for timer in deploy/systemd/*.timer; do
    sudo systemctl enable --now "$(basename "$timer")"
done

pip install -r requirements.txt
cd ifiplatform
# Some migrations are forward-only; their way back is this backup. If the
# backup fails, set -e stops the deploy before anything is migrated.
bash ../deploy/backup/backup_db.sh
python manage.py migrate
python manage.py collectstatic --noinput --clear

# DeepL glossaries can't be edited, only recreated -- so only re-sync when
# the terms changed. A failure keeps the old glossary instead of aborting.
if ! git diff --quiet "$OLD_SHA" HEAD -- apps/ifi_home_app/translation/glossary_terms.py; then
    python manage.py sync_deepl_glossary --write-env \
        || echo "WARNING: sync_deepl_glossary failed -- still using the previous DEEPL_GLOSSARY_ID."
fi

sudo systemctl restart gunicorn
python manage.py clear_cache              # after the restart, see clear_cache's docstring
python manage.py announce_deploy --clear  # remove the visitor banner

# Only reports drift between deploy/server_config/ and the live files; a
# problem here must never fail a deploy that has already gone out.
bash ../deploy/check_server_config.sh || true

echo "Deploy complete."
