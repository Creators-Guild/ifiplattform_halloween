"""Creates the event issues on GitHub from out/ (made by generate.py), with the
`gh` CLI. Run it on a computer where `gh auth login` is done:

    python3 create_issues.py --repo Creators-Guild/ifiplattform_halloween --dry-run
    python3 create_issues.py --repo Creators-Guild/ifiplattform_halloween

Steps:
1. Makes sure the size and category labels exist (`gh label create --force`).
2. Creates every issue with its title, labels and type, and a placeholder body.
3. Now that every ID has a number, writes the real titles and bodies: IDs
   like "P10a" or "SET-moon" become "#12", and "{number}" becomes the issue's
   own number.
4. Makes the sub-issues of each set (REST: POST .../issues/<parent>/sub_issues),
   skipping the ones a set already has.
5. Writes out/numbers.json (ID -> number) and out/solutions.json, ready for
   `manage.py load_event_solutions < solutions.json`.

Stops at the first error. Already created issues are remembered in
out/numbers.json, so running it again continues instead of making copies.
Running it again after changing issues/ updates every title and body; labels
and type are only set when an issue is created. Keep numbers.json: without
it, a new run makes every issue again."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from generate import SIZE_LABEL, load

HERE = Path(__file__).parent
OUT = HERE / "out"
NUMBERS = OUT / "numbers.json"

LABEL_COLOURS = {
    "🍬 candy": "f9a8d4", "🍫 chocolate": "7c4a2d", "🎃 pumpkin": "ff7518",
    "🎨 restyle": "a78bfa", "🦇 silly feature": "6b7280", "🧪 python": "3fa33f",
    "✍️ content": "fbbf24", "🔤 text": "60a5fa", "🖼️ art": "f472b6",
    "📚 docs": "0ea5e9", "👻 haunted bug": "e5e7eb", "♿ a11y": "2563eb",
}


def run(args, dry, capture=False):
    print("  $ " + " ".join(a if " " not in a else repr(a) for a in args))
    if dry:
        return "0" if capture else None
    result = subprocess.run(args, check=True, capture_output=capture, text=True)
    return result.stdout.strip() if capture else None


def link_ids(text, numbers):
    """P10a -> #12, longest IDs first so P10a isn't read as P1 + "0a".
    Code blocks are left alone: SVG paths like "Q15,42" look like IDs."""
    parts = re.split(r"(^```.*?^```[^\n]*$)", text, flags=re.M | re.S)
    for i in range(0, len(parts), 2):
        for issue_id in sorted(numbers, key=len, reverse=True):
            parts[i] = re.sub(rf"(?<![\w#-]){re.escape(issue_id)}(?![\w-])", f"#{numbers[issue_id]}", parts[i])
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dry, repo = args.dry_run, args.repo
    issues = load()
    numbers = json.loads(NUMBERS.read_text()) if NUMBERS.exists() and not dry else {}

    print("1. Labels")
    for label in sorted({SIZE_LABEL[m["size"]] for m in issues.values()} | {m["category"] for m in issues.values()}):
        run(["gh", "label", "create", label, "--repo", repo, "--force", "--color", LABEL_COLOURS.get(label, "cccccc")], dry)

    print("2. Issues")
    for fake, (issue_id, meta) in enumerate(issues.items(), start=1000):
        if issue_id in numbers:
            continue
        number = run([
            "gh", "api", f"repos/{repo}/issues", "-X", "POST",
            "-f", f"title={meta['title']}", "-f", "body=(being written...)",
            "-f", f"type={meta['type']}",
            "-f", f"labels[]={SIZE_LABEL[meta['size']]}", "-f", f"labels[]={meta['category']}",
            "--jq", ".number",
        ], dry, capture=True)
        numbers[issue_id] = fake if dry else int(number)
        if not dry:
            NUMBERS.write_text(json.dumps(numbers, indent=2) + "\n")

    print("3. Bodies")
    for issue_id in issues:
        body = (OUT / "bodies" / f"{issue_id}.md").read_text().replace("{number}", str(numbers[issue_id]))
        body = link_ids(body, numbers)
        path = OUT / "bodies_final" / f"{issue_id}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(body)
        run(["gh", "issue", "edit", str(numbers[issue_id]), "--repo", repo,
             "--title", issues[issue_id]["title"], "--body-file", str(path)], dry)

    print("4. Sub-issues")
    existing = {}
    for issue_id, meta in issues.items():
        parent = meta.get("parent")
        if not parent:
            continue
        if parent not in existing:
            # GitHub refuses a sub-issue the set already has, which would stop a second run here.
            listed = run(["gh", "api", "--paginate", f"repos/{repo}/issues/{numbers[parent]}/sub_issues",
                          "--jq", ".[].number"], dry, capture=True)
            existing[parent] = set() if dry else {int(n) for n in listed.split()}
        if numbers[issue_id] in existing[parent]:
            continue
        child_id = run(["gh", "api", f"repos/{repo}/issues/{numbers[issue_id]}", "--jq", ".id"], dry, capture=True)
        run(["gh", "api", f"repos/{repo}/issues/{numbers[parent]}/sub_issues", "-X", "POST", "-F", f"sub_issue_id={child_id}"], dry)

    print("5. Solutions")
    solutions = json.loads((OUT / "solutions_by_id.json").read_text())
    final = [
        {"issue": numbers[s["id"]], "note": link_ids(s["note"], numbers), "diff": s["diff"]}
        for s in solutions
    ]
    target = OUT / ("solutions.dry-run.json" if dry else "solutions.json")
    target.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
    print(f"Done: {len(numbers)} issues. Solutions in {target}")


if __name__ == "__main__":
    sys.exit(main())
