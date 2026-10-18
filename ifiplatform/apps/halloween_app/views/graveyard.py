"""The graveyard of retired features in the Halloween corner: one tombstone
for every feature the site used to have. Half built: the page shows the
graves, filling the graveyard is the event issue's job (the TODO)."""

from django.shortcuts import render

GRAVES = [
    {
        "name": "Your Page",
        "born": "2026",
        "died": "15 Oct 2026",
        "epitaph": "Renamed to Commits. It lives on under a new name.",
    },
    # TODO: at least 5 more graves, for features that really were removed
    # from the site. Find them in the Git history.
]


def graveyard_view(request):
    return render(request, "halloween/graveyard.html", {"graves": GRAVES})
