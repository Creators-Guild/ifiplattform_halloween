"""The fortune teller in the Halloween corner. Half built: the page and the
form work, the fortune itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

from ..fortune_names import clean_name

FORTUNES = [
    "A ghost will fix your next merge conflict.",
    # TODO 1: add at least 7 more spooky fortunes.
]


def pick_fortune(name):
    """The same name always gets the same fortune."""
    # TODO 2: turn clean_name(name) into a number (for example the sum of
    # ord() of every letter), and use % len(FORTUNES) to pick a fortune.
    return None


def fortune_view(request):
    name = request.GET.get("name", "").strip()
    fortune = pick_fortune(name) if name else None
    return render(request, "halloween/fortune.html", {"name": name, "fortune": fortune})
