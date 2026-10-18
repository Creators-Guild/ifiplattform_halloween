"""The graveyard of retired features in the Halloween corner: one tombstone
for every feature the site used to have. Found with
git log --diff-filter=D --name-only (every commit that deleted files)."""

from django.shortcuts import render

GRAVES = [
    {
        "name": "Your Page",
        "born": "2026",
        "died": "15 Oct 2026",
        "epitaph": "Renamed to Commits. It lives on under a new name.",
    },
    {
        "name": "Your subjects",
        "born": "2026",
        "died": "15 Oct 2026",
        "epitaph": "Knew every course you took. Took the secret to the grave.",
    },
    {
        "name": "The pull request template",
        "born": "2026",
        "died": "16 Oct 2026",
        "epitaph": "Asked everyone to fill in a checklist. Nobody did.",
    },
    {
        "name": "Trello sync",
        "born": "2026",
        "died": "14 Oct 2026",
        "epitaph": "Moved cards around at night. Now it rests on GitHub.",
    },
    {
        "name": "Translate a whole page tree",
        "born": "2026",
        "died": "14 Oct 2026",
        "epitaph": "Spoke every language for a single day.",
    },
    {
        "name": "The second Docker guide",
        "born": "2026",
        "died": "15 Oct 2026",
        "epitaph": "Merged with its twin. Together forever in one guide.",
    },
]


def graveyard_view(request):
    return render(request, "halloween/graveyard.html", {"graves": GRAVES})
