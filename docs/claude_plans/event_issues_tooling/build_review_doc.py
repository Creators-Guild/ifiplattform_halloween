"""Writes docs/claude_plans/event_issues_<size>.md, one review doc per
difficulty (each issue with a screenshot), and copies the screenshots next
to them. A set goes in the doc for its own size, which is also the size of
all its sub-issues."""

import shutil
import sys
from pathlib import Path

from generate import SIZE_LABEL, final_body, load

HERE = Path(__file__).parent
DOCS = Path(sys.argv[1])
IMAGES = DOCS / "event_issues_images"

CAPTIONS = {
    "P2": "Mock-up: a screenshot can't show the mouse pointer, so the bat is drawn in where the pointer would be.",
    "P3": "The dev database has only 2 news articles, so the limit of 8 doesn't change anything you can see here.",
    "P6": "Mock-up: the new icon in a browser tab, and large.",
    "P7": "The new section of the CSS README.",
    "P9": "After pressing Tab: the focused shortcut (Info) has an outline.",
    "P10a": "Only this step: the moon without craters or glow.",
    "P10b": "The moon with craters, without the glow (that's P10c).",
    "K3": "The ghost, caught halfway across the page.",
    "K5": "Logged in: the account button in the header.",
    "K19": "Terminal output.",
    "K28": "Mock-up: what changes. A screenshot of something that doesn't move looks like nothing.",
    "K30": "After pressing English on a Norwegian article: the same article, in English. The bar on top shows the address.",
    "Q5": "Mid-game: one bat hit, the next one showing.",
    "Q7": "One pair found (🎃), one card turned over.",
    "Q22": "Terminal output.",
    "Q28": "The fortune teller with the name Åse, which used to crash.",
    "Q29": "One note dragged out of place; \"Tidy the board\" puts it back.",
    "C10": "Caught mid-wiggle: the mouse is over Foreninger.",
    "C27": "Only this step: the thread and the body, without the legs.",
    "C29": "The swing, paused at one end.",
    "C30": "Mock-up: what changes. A screenshot of something that doesn't move looks like nothing.",
    "C31": "The fixed lines. The dev database has no events today or tomorrow, so the page itself shows only weekdays.",
    "C33": "The fixed lines. The cards look the same; only what screen readers hear changes.",
    "K4": "Right after a click: the spider has climbed up its thread.",
    "K8": "Real hours, checked on 18 October 2026. Sunday, so two places are closed today.",
    "K12": "After a click on \"Trick or Treat?\".",
    "K13": "Halfway through the spin, after typing b o o.",
    "K27": "The times, dates and \"Se alle arrangementer\" now readable on grey.",
    "K34": "Three bats on their way out of the moon, paused mid-flight.",
    "Q6": "Mid-game: two zombies walking in, a word half typed.",
    "Q8": "After Shuffle.",
    "Q9": "Mid-game: the bat flying up, a candy on the right.",
    "Q10": "After checking the answers, with three right.",
    "Q13": "A carved face, with the candle lit.",
    "Q16": "The moon on 18 October 2026: just under half full, growing.",
    "Q17": "The new tests.",
    "Q18": "The ghost following the pointer (the pointer itself doesn't show in a screenshot).",
    "Q19": "Two seconds after typing the code.",
    "Q20": "Flashlight on, pointed at the shortcuts.",
    "Q24": "The six faces under the carver.",
    "Q26": "The badges' new colours. Below: the orange focus ring in the header, after pressing Tab.",
    "K36": "After pressing 👍 on this excuse.",
    "K37": "Right after pressing Copy.",
    "K38": "The new tests, run against the ten joke files.",
    "Q32": "After pressing \"Give me another excuse\": a new excuse, same page, no reload.",
    "Q27": "The skip link and the \"All pages\" heading show; the rest is what screen readers hear.",
}


def main():
    issues = load()
    if IMAGES.exists():
        shutil.rmtree(IMAGES)
    IMAGES.mkdir(parents=True)
    for size, label in SIZE_LABEL.items():
        sized = {i: m for i, m in issues.items() if m["size"] == size}
        sets = sum(1 for i in sized if i.startswith("SET-"))
        parts = [
            f"# Commit for Candy: {label} issues (for review)\n",
            f"The {len(sized)} {label} event issues ({len(sized) - sets} to claim, {sets} sets) exactly as "
            "they will be posted on GitHub, generated on 2026-10-18. The other sizes are in "
            + " and ".join(f"[event_issues_{s}.md](event_issues_{s}.md)" for s in SIZE_LABEL if s != size)
            + ". Under each issue is a screenshot of what it looks like when it's done, taken from the site "
            "with every issue done. Issues refer to each other by ID (P10a, SET-moon); the creation script "
            "turns those into issue numbers. Delete these files and their image folder once the issues are "
            "on GitHub.\n",
        ]
        for issue_id, meta in sized.items():
            parts.append("---\n")
            parts.append(f"# {issue_id}: {meta['title']}\n`{label}` · `{meta['category']}` · {meta['type']}\n")
            parts.append(final_body(meta))
            shot = HERE / "shots" / f"{issue_id}.jpg"
            if shot.exists():
                shutil.copy(shot, IMAGES / shot.name)
                caption = CAPTIONS.get(issue_id, "")
                parts.append(
                    f"#### What it looks like when it's done\n![{issue_id} done]({IMAGES.name}/{shot.name})\n"
                    + (f"\n*{caption}*\n" if caption else "")
                )
            extra = HERE / "shots" / f"{issue_id}-focus.jpg"
            if extra.exists():
                shutil.copy(extra, IMAGES / extra.name)
                parts.append(f"![{issue_id} focus]({IMAGES.name}/{extra.name})\n")
        out = DOCS / f"event_issues_{size}.md"
        out.write_text("\n".join(parts))
        print(f"wrote {out} with {len(sized)} issues")
    print(f"copied {len(list(IMAGES.iterdir()))} images to {IMAGES}")

if __name__ == "__main__":
    main()
