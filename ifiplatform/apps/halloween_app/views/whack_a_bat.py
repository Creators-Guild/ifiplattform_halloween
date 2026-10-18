# pylint: disable=C0114
from django.shortcuts import render


def whack_a_bat_view(request):
    """Whack-a-bat: the game itself is static/js/halloween_pages/whack_a_bat.js."""
    return render(request, "halloween/whack_a_bat.html", {"holes": range(9)})
