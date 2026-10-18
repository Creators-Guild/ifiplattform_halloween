"""The spooky name generator in the Halloween corner. Half built: the page
and the form work, the name itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

FIRST_PARTS = [
    "Count",
    "Lady",
    "Doctor",
    "Old",
    "Baron",
    "Little",
]
LAST_PARTS = [
    "of the Crypt",
    "Bonecrusher",
    "the Pale",
    "of the Haunted Lab",
    "Nightshade",
    "the Restless",
]


def spooky_name(name):
    """ "Kari" -> for example "Count Kari of the Crypt". The same name always
    gets the same spooky name."""
    first = FIRST_PARTS[len(name) % len(FIRST_PARTS)]
    last = LAST_PARTS[sum(ord(c) for c in name.lower()) % len(LAST_PARTS)]
    return f"{first} {name} {last}"


def spooky_name_view(request):
    name = request.GET.get("name", "").strip()
    result = spooky_name(name) if name else None
    return render(request, "halloween/spooky_name.html", {"name": name, "result": result})
