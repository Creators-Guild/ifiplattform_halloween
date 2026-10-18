"""Builds everything the event issues need from issues/*.md:
- out/bodies/<ID>.md: the final issue body (reward, time, set, text, how-to),
- out/all_issues.md: every issue in one file, for review,
- out/solutions_by_id.json: the helpers' solutions (note + diff), by ID.
Issue IDs like P10a or SET-moon in the texts become "#<number>" when
create_issues.py creates them on GitHub. Diffs come from the tested solution
branches in pilot_repo (one branch per ID)."""

import json
import re
import subprocess
from pathlib import Path

from helper_notes import NOTES

HERE = Path(__file__).parent
REPO = HERE / "pilot_repo"
OUT = HERE / "out"

REWARD = {"candy": "1 🪙", "chocolate": "2 🪙 + 2 🏆", "pumpkin": "3 🪙 + 3 🏆"}
SIZE_LABEL = {"candy": "🍬 candy", "chocolate": "🍫 chocolate", "pumpkin": "🎃 pumpkin"}

HOW_TO = """
### How to work on it
Set up the project on your own computer first (see **Get started** in the README). Then:

1. **Claim this issue** on the site: https://halloween.ifiplattform.no/commits/issues/
2. In the VS Code terminal:
   ```bash
   ifi fix-issue {number}
   ```
3. Make the change, and check it at http://localhost:8000. Reload with **Ctrl+Shift+R** (Mac: **Cmd+Shift+R**): a normal reload may show the old look, because the browser keeps old copies of CSS files and pictures. Still old? Try a private window.
4. Then:
   ```bash
   ifi test
   git add .
   git commit -m "Short description of what you changed"
   ifi pull-request
   ```

**Only change the files listed above.** Then your pull request can't clash with anyone else's. After the merge it can take a few minutes before it shows on the live site. Stuck? Ask a helper, or type `ifi help`.
"""


def read_issue(path):
    text = path.read_text()
    _, front, body = text.split("---\n", 2)
    meta = dict(line.split(": ", 1) if ": " in line else (line.rstrip(":"), "") for line in front.strip().splitlines())
    meta["body"] = body.strip()
    return meta


def load():
    issues = {}
    for path in sorted(HERE.glob("issues/*.md")):
        meta = read_issue(path)
        issues[meta["id"]] = meta
    return issues


def final_body(meta):
    if meta["id"].startswith("SET-"):
        return meta["body"] + "\n"
    head = f"**Reward:** {REWARD[meta['size']]} · **Time:** about {meta['minutes']} min"
    if meta.get("parent"):
        head += f" · **Part of the set** {meta['parent']}"
    head += f"  \n**Good to know first:** {meta['knowledge']}"
    return f"{head}\n\n{meta['body']}\n{HOW_TO}"


def diff_for(issue_id):
    return subprocess.run(
        ["git", "diff", f"scaffold-base...{issue_id}"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout


def files_line(diff):
    names = [line[len("+++ b/"):] for line in diff.splitlines() if line.startswith("+++ b/")]
    return f"Files: {', '.join(names)}\n\n" if names else ""


CHECK_PR = (
    "\n\nCheck the PR: the 'Files check' warns when the PR changes more than "
    "these files (extras on purpose are fine), and fails when the change was "
    "made in the browser on github.com: then help them set up locally "
    "instead of merging. Accidental extra files (a .po file, a migration, "
    "db.sqlite3) should go: `git restore --source=upstream/main <file>` "
    "(collaborators: origin/main), or `git rm --cached <file>` for a new "
    "file, then commit and push again."
)


def main():
    issues = load()
    phase1 = {e["key"]: e for e in json.loads((HERE / "phase1_solutions_draft.json").read_text())}
    (OUT / "bodies").mkdir(parents=True, exist_ok=True)
    review = []
    solutions = []
    for issue_id, meta in issues.items():
        body = final_body(meta)
        (OUT / "bodies" / f"{issue_id}.md").write_text(body)
        size = SIZE_LABEL[meta["size"]]
        review.append(f"# {issue_id}: {meta['title']}\n`{size}` · `{meta['category']}` · {meta['type']}\n\n{body}\n\n---\n")
        if issue_id.startswith("SET-"):
            note, diff = NOTES[issue_id], ""
        else:
            diff = diff_for(issue_id)
            note = NOTES.get(issue_id) or phase1[issue_id]["note"].split("\n\nCheck the PR:")[0].split("\n\n", 1)[1]
            note = files_line(diff) + note + CHECK_PR
        solutions.append({"id": issue_id, "note": note, "diff": diff})
    (OUT / "all_issues.md").write_text("\n".join(review))
    (OUT / "solutions_by_id.json").write_text(json.dumps(solutions, ensure_ascii=False, indent=2) + "\n")
    sizes = {}
    for meta in issues.values():
        if not meta["id"].startswith("SET-"):
            sizes[meta["size"]] = sizes.get(meta["size"], 0) + 1
    print(f"{len(issues)} issues ({sizes}, {sum(1 for i in issues if i.startswith('SET-'))} sets) -> {OUT}")


if __name__ == "__main__":
    main()
