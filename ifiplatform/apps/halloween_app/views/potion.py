"""The potion mixer in the Halloween corner. Half built: the page and the
form work, what the potion turns into is the event issue's job (the TODOs)."""

from django.shortcuts import render

INGREDIENTS = [
    ("bat_wing", "🦇 Bat wing"),
    ("pumpkin", "🎃 Pumpkin"),
    ("spider", "🕷️ Spider"),
    ("eyeball", "👁️ Eyeball"),
    ("candy", "🍬 Candy"),
    ("coffee", "☕ Cold coffee from the 3rd floor"),
]


def mix(picked):
    """The picked ingredient keys -> what the potion does, as one sentence."""
    # TODO 1: nothing picked -> "Just water. Spooky.".
    # TODO 2: at least 4 rules for special combinations, for example
    #         bat_wing + coffee -> "You can now debug all night."
    # TODO 3: anything else -> a general sentence that names how many
    #         ingredients went in.
    return None


def potion_view(request):
    keys = {key for key, _label in INGREDIENTS}
    picked = [key for key in request.GET.getlist("ingredient") if key in keys]
    result = mix(picked) if "brew" in request.GET else None
    return render(
        request,
        "halloween/potion.html",
        {"ingredients": INGREDIENTS, "picked": picked, "result": result},
    )
