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
    if len(picked) == 0:
        return "Just water. Spooky."
    
    if "bat_wing" in picked and "coffee" in picked:
        return "You can now debug all night."
    if "pumpkin" in picked and "candy" in picked:
        return "A sweet and spooky surprise awaits you!"
    if "spider" in picked and "eyeball" in picked:
        return "You can now see through walls, but beware of the spiders!"
    if "bat_wing" in picked and "spider" in picked:
        return "You can now fly through the night like a spooky bat!"

    return f"A mysterious potion with {len(picked)} ingredients. What could it do?"


def potion_view(request):
    keys = {key for key, _label in INGREDIENTS}
    picked = [key for key in request.GET.getlist("ingredient") if key in keys]
    result = mix(picked) if "brew" in request.GET else None
    return render(
        request,
        "halloween/potion.html",
        {"ingredients": INGREDIENTS, "picked": picked, "result": result},
    )
