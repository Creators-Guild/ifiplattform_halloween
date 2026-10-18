"""The fortune teller in the Halloween corner. Half built: the page and the
form work, the fortune itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

from ..fortune_names import clean_name

FORTUNES = [
    "A ghost will fix your next merge conflict.",
    "Your code will compile on the first try. Be afraid.",
    "A black cat will cross your keyboard at the worst possible moment.",
    "Tonight, a bug you fixed last year comes back.",
    "You will find an empty group room. It was never empty.",
    "The printer will work for you, and only for you, today.",
    "A pumpkin is watching your Git history.",
    "Your next deadline is closer than it appears.",
]


def pick_fortune(name):
    """The same name always gets the same fortune."""
    number = sum(ord(letter) for letter in clean_name(name))
    return FORTUNES[number % len(FORTUNES)]


def fortune_view(request):
    name = request.GET.get("name", "").strip()
    fortune = pick_fortune(name) if name else None
    return render(request, "halloween/fortune.html", {"name": name, "fortune": fortune})
