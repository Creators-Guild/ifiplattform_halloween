#!/usr/bin/env bash
# Prepares a fresh Ubuntu 24.04 server for the Docker setup. Run once, from
# the cloned repo:
#   sudo bash deploy/docker/setup_server.sh
# Then log out and back in, so your user can run docker without sudo.
# Guide: docs/operations/docker_server.md.
#
# Safe to run again: each step skips what's already done. Running it again
# also installs the current fail2ban rules from the repo.

set -euo pipefail
cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this with sudo: sudo bash deploy/docker/setup_server.sh" >&2
    exit 1
fi
USER_NAME=${SUDO_USER:-ubuntu}

echo "== Installing Docker and fail2ban"
apt-get update
apt-get install -y docker.io docker-compose-v2 fail2ban
systemctl enable --now docker

echo "== Letting $USER_NAME use Docker without sudo"
usermod -aG docker "$USER_NAME"

echo "== Installing the fail2ban rules"
install -m 644 fail2ban/jail.local /etc/fail2ban/jail.local
systemctl restart fail2ban

echo "== Swap"
# Extra memory on disk, so building an image can't run the server out of memory.
if [ -z "$(swapon --show --noheadings)" ]; then
    if [ ! -f /swapfile ]; then
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
    fi
    swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
else
    echo "Already has swap, skipping."
fi

echo "== Automatic security updates at 04:00"
# They can briefly restart Docker and so the site, so they run at night.
# The empty OnCalendar= clears Ubuntu's default time.
mkdir -p /etc/systemd/system/apt-daily-upgrade.timer.d
cat > /etc/systemd/system/apt-daily-upgrade.timer.d/override.conf <<'EOF'
[Timer]
OnCalendar=
OnCalendar=*-*-* 04:00
RandomizedDelaySec=30m
EOF
systemctl daemon-reload

echo "Done. Log out and back in, then follow the next steps in docs/operations/docker_server.md."
