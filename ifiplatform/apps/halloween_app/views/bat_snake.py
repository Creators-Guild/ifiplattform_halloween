# pylint: disable=C0114
from django.shortcuts import render


def bat_snake_view(request):
    """The bat snake game: the game itself is static/js/halloween_pages/bat_snake.js."""
    return render(request, "halloween/bat_snake.html")
