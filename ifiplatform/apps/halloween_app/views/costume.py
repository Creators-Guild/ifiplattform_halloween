"""The costume generator in the Halloween corner. Half built: the button
works, the costume itself is the event issue's job (the TODOs)."""

import random

from django.shortcuts import render

LOOKS = [
    "glow-in-the-dark",
    # TODO 1: add at least 4 more, like "tiny", "soaking wet", "very polite".
]
CREATURES = [
    "vampire",
    # TODO 1: add at least 4 more, like "mummy", "haunted printer".
]
EXTRAS = [
    "with a laptop",
    # TODO 1: add at least 4 more, like "on roller skates".
]


def make_costume():
    """A random costume as one sentence, for example
    "A glow-in-the-dark vampire with a laptop"."""
    # TODO 2: pick one word from each list (random.choice) and put them
    # together into a sentence.
    return None


def costume_view(request):
    rolled = "roll" in request.GET
    costume = make_costume() if rolled else None
    return render(request, "halloween/costume.html", {"rolled": rolled, "costume": costume})
