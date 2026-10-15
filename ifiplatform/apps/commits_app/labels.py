"""The label contract with the event issues on GitHub: which labels make an
issue count, and for how many points. Rename here when the labels change --
the sync (github_sync.py) and the pages both read it."""

from django.utils.translation import gettext as _

SIZE_LABELS = {
    "🍬 candy": ("candy", 1),
    "🍫 chocolate": ("chocolate", 2),
    "🎃 pumpkin": ("pumpkin", 3),
}
CATEGORY_LABELS = [
    "🎨 restyle",
    "🦇 silly feature",
    "🧪 python",
    "✍️ content",
    "🔤 text",
    "🖼️ art",
    "📚 docs",
    "👻 haunted bug",
    "♿ a11y",
]

# A CSS-safe name per category, for colouring its cards
# (issue_list.css: .issue-list__item--<slug>).
CATEGORY_SLUGS = {
    "🎨 restyle": "restyle",
    "🦇 silly feature": "silly",
    "🧪 python": "python",
    "✍️ content": "content",
    "🔤 text": "text",
    "🖼️ art": "art",
    "📚 docs": "docs",
    "👻 haunted bug": "haunted",
    "♿ a11y": "a11y",
}


def size_label(size):
    """ "candy" -> "🍬 candy", for showing a size on the cards."""
    return next((label for label, (name, _) in SIZE_LABELS.items() if name == size), "")


def difficulty_text(size):
    """ "candy" -> "🍬 candy (easy)", as the Difficulty filter shows it."""
    return dict(difficulty_choices()).get(size, "")


def difficulty_choices():
    """(size, text) pairs for the issue list's Difficulty filter, easiest first."""
    words = {1: _("easy"), 2: _("medium"), 3: _("hard")}
    return [
        (name, f"{label} ({words.get(points, points)})")
        for label, (name, points) in sorted(SIZE_LABELS.items(), key=lambda i: i[1][1])
    ]
