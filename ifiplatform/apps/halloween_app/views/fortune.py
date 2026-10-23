"""The fortune teller in the Halloween corner. Half built: the page and the
form work, the fortune itself is the event issue's job (the TODOs)."""

from django.shortcuts import render

from ..fortune_names import clean_name

FORTUNES = [
    "A ghost will fix your next merge conflict.",
    "A sleek, mysterious visitor will cross your path soon, bringing an unexpected stroke of good luck.",
    "A shadowy figure will appear in your dreams tonight, whispering secrets of the future.",
    "Beware of the black cat that crosses your path; it may be a harbinger of change.",
    "The spirits of the past will guide you to a hidden treasure.",
    "A chilling wind will bring a message from the beyond.",
    "Your next Halloween costume will be more than just a disguise; it will reveal your true self.",
    "A mix of hard work and wild imagination will soon bubble over into a major success.",
]


def pick_fortune(name):
    """The same name always gets the same fortune."""
    number = sum(ord(letter) for letter in clean_name(name))
    picked_up = FORTUNES[number % len(FORTUNES)]
    return picked_up


def fortune_view(request):
    name = request.GET.get("name", "").strip()
    fortune = pick_fortune(name) if name else None
    return render(request, "halloween/fortune.html", {"name": name, "fortune": fortune})
