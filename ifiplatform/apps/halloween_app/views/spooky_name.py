"""The spooky name generator in the Halloween corner. Half built: the page
and the form work, the name itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

FIRST_PARTS = [
    "Count",
    # TODO 1: add at least 5 more, like "Lady", "Doctor", "Old".
]
LAST_PARTS = [
    "of the Crypt",
    # TODO 2: add at least 5 more, like "Bonecrusher", "the Pale".
]


def spooky_name(name):
    """ "Kari" -> for example "Count Kari of the Crypt". The same name always
    gets the same spooky name."""
    # TODO 3: pick one of FIRST_PARTS and one of LAST_PARTS from the name
    # (for example len(name) and the sum of ord() of the letters), and put
    # the name in between.
    return None


def spooky_name_view(request):
    name = request.GET.get("name", "").strip()
    result = spooky_name(name) if name else None
    return render(request, "halloween/spooky_name.html", {"name": name, "result": result})
