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
    picked = set(picked)
    if not picked:
        return "Just water. Spooky."
    if picked == {"bat_wing", "coffee"}:
        return "You can now debug all night."
    if picked == {"pumpkin", "candy"}:
        return "Pumpkin spice potion: everyone at Ifi wants a sip."
    if picked == {"spider", "eyeball"}:
        return "You can now see every bug in your code. All of them. Forever."
    if "eyeball" in picked and "coffee" in picked:
        return "Your eyes will stay open through the whole lecture."
    return f"The cauldron swallows {len(picked)} ingredient(s) and burps a purple cloud."


def potion_view(request):
    keys = {key for key, _label in INGREDIENTS}
    picked = [key for key in request.GET.getlist("ingredient") if key in keys]
    result = mix(picked) if "brew" in request.GET else None
    return render(
        request,
        "halloween/potion.html",
        {"ingredients": INGREDIENTS, "picked": picked, "result": result},
    )
