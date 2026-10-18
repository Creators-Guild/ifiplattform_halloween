#!/usr/bin/env bash
# One-time setup for screenshots without root: Playwright in pwenv/, the
# Chromium libraries and fonts unpacked from Debian packages into debs/
# (fetch_debs.py), and shot_env.sh with the paths to source before shoot.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
python3 -m venv pwenv
pwenv/bin/pip -q install playwright==1.47.0
PLAYWRIGHT_BROWSERS_PATH="$HERE/pwenv/browsers" pwenv/bin/python -m playwright install chromium || true
python3 -I fetch_debs.py
R="$HERE/debs/root"
cat > debs/fonts.conf <<CONF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>$R/usr/share/fonts</dir>
  <cachedir>$HERE/debs/fontcache</cachedir>
  <include ignore_missing="yes">$R/etc/fonts/conf.d</include>
</fontconfig>
CONF
cat > shot_env.sh <<ENV
export LD_LIBRARY_PATH=$R/usr/lib/x86_64-linux-gnu:$R/lib/x86_64-linux-gnu
export FONTCONFIG_FILE=$HERE/debs/fonts.conf
export PLAYWRIGHT_BROWSERS_PATH=$HERE/pwenv/browsers
ENV
echo "Done. Before shoot.py: source $HERE/shot_env.sh"
