#!/usr/bin/env bash
# Deploys the Docker setup on a server: the first time, and on every
# update. Run on the server, from anywhere:
#   bash deploy/docker/deploy.sh
# Guide: docs/operations/docker_server.md.
#
# Runs in two parts:
#   1. On the old copy of this script: pull the new code.
#   2. Re-runs itself from the freshly pulled copy (--after-reset) and does
#      the rest, so edits to this file take effect in the same deploy.

set -eo pipefail
cd "$(dirname "$0")/../.."   # repo root

if [ ! -f .env ]; then
    echo "No .env in $(pwd). Copy deploy/docker/.env.example to .env and fill it in." >&2
    exit 1
fi

# Reads one value from .env without running the file as a script. A
# missing key gives an empty value instead of stopping the script.
env_value() {
    { grep -E "^$1=" .env || true; } | tail -n 1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//'
}

# Set here too, so a .env without COMPOSE_FILE can never start the local
# dev setup (docker-compose.yml) on a server.
export COMPOSE_FILE=compose.prod.yml

if [ "$1" != "--after-reset" ]; then
    BRANCH=$(env_value DEPLOY_BRANCH)
    BRANCH=${BRANCH:-main}
    git fetch origin "$BRANCH"
    git reset --hard "origin/$BRANCH"
    exec bash deploy/docker/deploy.sh --after-reset
fi

docker compose build
docker compose up -d db
docker compose run --rm -T web python manage.py migrate --noinput

SEED_COMMAND=$(env_value SEED_COMMAND)
if [ -n "$SEED_COMMAND" ]; then
    docker compose run --rm -T web python manage.py "$SEED_COMMAND"
fi

docker compose up -d
docker compose exec -T web python manage.py clear_cache   # after the restart, see clear_cache's docstring

# Old images and week-old build cache, so the disk doesn't fill up.
docker image prune -f
docker builder prune -f --filter until=168h

echo "Deploy complete."
