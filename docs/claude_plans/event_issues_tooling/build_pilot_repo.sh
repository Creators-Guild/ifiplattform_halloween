#!/usr/bin/env bash
# Rebuilds pilot_repo/: a throwaway clone of this repo where
# - "scaffold-base" is the repo as it is now, uncommitted changes included,
# - every issue has a branch with its solution (from solutions/ and
#   phase1_solutions/),
# - "all-merged" merges every issue branch: the conflict test.
# Then checks that each branch changes exactly the files its issue lists.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
R="$HERE/pilot_repo"
G="git -c user.name=pilot -c user.email=pilot@example.com"

rm -rf "$R"
git clone -q "$REPO" "$R"
cd "$R"
git checkout -q "$(git -C "$REPO" branch --show-current)"
(cd "$REPO" && git diff HEAD) | git apply --allow-empty
(cd "$REPO" && git ls-files --others --exclude-standard -z | tar cf - --null -T -) | tar xf -
cp "$REPO/ifiplatform/.env" ifiplatform/ 2>/dev/null || true
git add -A
$G commit -qm "scaffold" --allow-empty
git branch -f scaffold-base

for patch in "$HERE"/phase1_solutions/*.patch; do
    id="$(basename "$patch" .patch | sed 's/^p/P/')"
    git switch -q -c "$id" scaffold-base
    git apply "$patch"
    git add -A && $G commit -qm "$id"
done
for dir in "$HERE"/solutions/*/; do
    id="$(basename "$dir")"
    git switch -q -c "$id" scaffold-base
    cp -r "$dir". .
    git add -A && $G commit -qm "$id"
done

ids="$(ls "$HERE/issues" | sed 's/\.md$//' | grep -v '^SET-')"
git switch -q -c all-merged scaffold-base
# shellcheck disable=SC2086
$G merge -q --no-edit $ids
echo "all-merged: $(echo $ids | wc -w) issue branches merged without conflicts"

python3 - "$HERE" <<'PY'
import re, subprocess, sys
from pathlib import Path
here = Path(sys.argv[1])
bad = 0
for f in sorted((here / "issues").glob("*.md")):
    if f.stem.startswith("SET-"):
        continue
    block = re.split(r"^#{1,6} ", re.split(r"^### Files to change.*$", f.read_text(), flags=re.M)[1], flags=re.M)[0]
    listed = set(re.findall(r"`([^`\s]+/[^`\s]+)`", block))
    changed = set(subprocess.run(["git", "diff", "--name-only", f"scaffold-base...{f.stem}"],
                                 cwd=here / "pilot_repo", capture_output=True, text=True, check=True).stdout.split())
    if listed != changed:
        bad += 1
        print(f.stem, "listed but not changed:", listed - changed, "changed but not listed:", changed - listed)
print("every branch changes exactly its listed files" if not bad else f"{bad} mismatches")
sys.exit(1 if bad else 0)
PY
