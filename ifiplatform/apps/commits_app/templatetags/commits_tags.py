"""Template tags for the Commits pages, e.g. the visitor's points in the tab bar."""

import re

from django import template
from django.utils.html import escape, urlize
from django.utils.safestring import mark_safe

from ..labels import CATEGORY_SLUGS
from ..models import GitHubLink
from ..permissions import can_see_solutions
from ..scoring import score_for

register = template.Library()


@register.simple_tag(takes_context=True)
def is_helper(context):
    """Helpers and organisers: they get Sync now in the tab bar."""
    return can_see_solutions(context["request"].user)


@register.inclusion_tag("core/my_points.html", takes_context=True)
def my_points(context):
    """The visitor's GitHub link and score, for the chip in the Commits tab
    bar (core/commits_nav.html). Counted like the leaderboard, so the two
    always agree."""
    user = context["request"].user
    if not user.is_authenticated:
        return {"show": False}
    link = GitHubLink.objects.filter(user=user).first()
    return {
        "show": True,
        "link": link,
        "score": score_for(link.github_login) if link else None,
    }


@register.filter
def claim_offer(message):
    """The issue number from a "claim-offer-<n>" message tag, or "": the
    similar free issue offered when someone was faster (core/messages.html)."""
    for tag in (message.extra_tags or "").split():
        if tag.startswith("claim-offer-"):
            return tag.removeprefix("claim-offer-")
    return ""


@register.filter
def category_slug(label):
    """The colour slug for a category label, or "" for anything else (a
    difficulty heading, say)."""
    return CATEGORY_SLUGS.get(label, "")


# The labelled paragraphs of a helper note (event_issues_tooling/generate.py).
NOTE_KINDS = {"Correct": "correct", "Check": "check", "Common mistakes": "mistakes"}


@register.filter
def solution_note(note):
    """A helper note split into its parts: files (the "Files:" list), items
    ([(label, kind, html)] for each "Label: text" paragraph; kind colours
    Correct, Check and Common mistakes, "other" for labels like "The planted
    bug") and other (paragraphs without a label). "Check the PR:" is
    dropped: the page shows that text itself, the same for every issue."""
    parts = {"files": [], "items": [], "other": []}
    for paragraph in re.split(r"\n\s*\n", (note or "").strip()):
        labelled = re.match(r"([A-Z][^:.`\n]{0,30}): (.*)", paragraph, re.S)
        label, text = labelled.groups() if labelled else ("", paragraph)
        if label == "Files":
            parts["files"] = [name.strip() for name in text.split(",") if name.strip()]
        elif label == "Check the PR":
            continue
        elif label:
            parts["items"].append((label, NOTE_KINDS.get(label, "other"), _note_html(text)))
        elif paragraph.strip():
            parts["other"].append(_note_html(paragraph))
    return parts


def _note_html(text):
    """Escaped text with `code` as <code> and links clickable."""
    pieces = re.split(r"`([^`]+)`", text)
    return mark_safe(
        "".join(
            f"<code>{escape(piece)}</code>" if i % 2 else urlize(piece, autoescape=True)
            for i, piece in enumerate(pieces)
        )
    )


@register.filter
def diff_files(diff):
    """A git diff as [{"path", "status", "lines": [(kind, text)]}], one per
    file. status is "new", "empty" (in the repo but empty, so the solution
    writes all of it), "deleted" or "changed". A new or empty file's lines
    are its contents (kind "plain", no "+"); otherwise kind is "add", "del" or
    "ctx" with the +/- kept, and "hunk" (text: the line number it starts
    at) between the parts of a file."""
    files, current, in_header = [], None, False
    for line in (diff or "").splitlines():
        if line.startswith("diff --git "):
            current = {"path": line.rsplit(" b/", 1)[-1], "status": "changed", "lines": []}
            files.append(current)
            in_header = True
        elif current is None or line.startswith("\\"):
            continue
        elif line.startswith("@@"):
            in_header = False
            start = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            if current["status"] == "changed" and line.startswith("@@ -0,0 "):
                current["status"] = "empty"
            elif current["status"] == "changed" and start:
                current["lines"].append(("hunk", start.group(1)))
        elif in_header:
            if line.startswith("new file mode") or line == "--- /dev/null":
                current["status"] = "new"
            elif line.startswith("deleted file mode") or line == "+++ /dev/null":
                current["status"] = "deleted"
            elif line.startswith("+++ b/"):
                current["path"] = line[len("+++ b/"):]
        elif current["status"] in ("new", "empty"):
            current["lines"].append(("plain", line[1:]))
        else:
            current["lines"].append(({"+": "add", "-": "del"}.get(line[:1], "ctx"), line))
    return files
