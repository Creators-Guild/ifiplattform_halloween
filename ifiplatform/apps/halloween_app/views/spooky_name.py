"""The spooky name generator in the Halloween corner. Half built: the page
and the form work, the name itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

FIRST_PARTS = [
    "Count",
    "Baron",
    "Lady",
    "Doctor",
    "Old",
    "Sir",
]
LAST_PARTS = [
    "of the Crypt",
    "the Pale",
    "of the Night",
    "the Bonecrusher",
    "of the Shadows",
    "the Undying",
]


def spooky_name(name):
    """ "Kari" -> for example "Count Kari of the Crypt". The same name always
    gets the same spooky name."""
    number = sum(ord(letter) for letter in name)
    first_part = FIRST_PARTS[number % len(FIRST_PARTS)]
    last_part = LAST_PARTS[number % len(LAST_PARTS)]
    return f"{first_part} {name} {last_part}"

def spooky_name_view(request):
    name = request.GET.get("name", "").strip()
    result = spooky_name(name) if name else None
    return render(request, "halloween/spooky_name.html", {"name": name, "result": result})
