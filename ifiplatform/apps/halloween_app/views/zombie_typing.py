# pylint: disable=C0114
from django.shortcuts import render


def zombie_typing_view(request):
    """The zombie typing game: the game itself is static/js/halloween_pages/zombie_typing.js."""
    return render(request, "halloween/zombie_typing.html")
