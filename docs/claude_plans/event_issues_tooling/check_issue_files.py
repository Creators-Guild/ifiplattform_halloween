"""Checks the event issue texts in issues/ against the repo:
- no file is listed by two issues (that would be a merge conflict),
- every listed file that isn't marked "new:" exists,
- every "new:" file doesn't exist yet.
Parses "### Files to change" the same way .github/workflows/files_check.yml does.
Usage: python3 check_issue_files.py <repo root>"""

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1])
ISSUES = Path(__file__).parent / "issues"

owners = defaultdict(list)
problems = []
for path in sorted(ISSUES.glob("*.md")):
    text = path.read_text()
    section = re.split(r"^### Files to change.*$", text, flags=re.M)
    if len(section) < 2:
        continue
    block = re.split(r"^#{1,6} ", section[1], flags=re.M)[0]
    for line in block.splitlines():
        for name in re.findall(r"`([^`\s]+/[^`\s]+)`", line):
            owners[name].append(path.stem)
            exists = (ROOT / name).exists()
            if line.lstrip("- ").startswith("new:") and exists:
                problems.append(f"{path.stem}: new file already exists: {name}")
            if not line.lstrip("- ").startswith("new:") and not exists:
                problems.append(f"{path.stem}: file to edit is missing: {name}")

for name, ids in owners.items():
    if len(ids) > 1:
        problems.append(f"{name} is in more than one issue: {', '.join(ids)}")

print(f"{len(owners)} files across {len(set(i for ids in owners.values() for i in ids))} issues")
print("\n".join(problems) or "OK: no shared files, every path as expected")
sys.exit(1 if problems else 0)
