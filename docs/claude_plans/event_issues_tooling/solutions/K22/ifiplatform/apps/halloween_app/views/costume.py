"""The costume generator in the Halloween corner: a random costume for the
party, from three lists of words."""

import random

from django.shortcuts import render

LOOKS = [
    "glow-in-the-dark",
    "tiny",
    "soaking wet",
    "very polite",
    "slightly haunted",
    "retro 8-bit",
]
CREATURES = [
    "vampire",
    "mummy",
    "haunted printer",
    "werewolf",
    "skeleton TA",
    "pumpkin",
]
EXTRAS = [
    "with a laptop",
    "on roller skates",
    "who only speaks in Python",
    "with a cape made of Post-its",
    "holding a cup of cold coffee",
    "with a merge conflict",
]


def make_costume():
    """A random costume as one sentence, for example
    "A glow-in-the-dark vampire with a laptop"."""
    return f"A {random.choice(LOOKS)} {random.choice(CREATURES)} {random.choice(EXTRAS)}"


def costume_view(request):
    rolled = "roll" in request.GET
    costume = make_costume() if rolled else None
    return render(request, "halloween/costume.html", {"rolled": rolled, "costume": costume})
