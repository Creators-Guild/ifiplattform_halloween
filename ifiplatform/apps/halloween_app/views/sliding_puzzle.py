# pylint: disable=C0114
from django.shortcuts import render


def sliding_puzzle_view(request):
    """The sliding puzzle game: the game itself is static/js/halloween_pages/sliding_puzzle.js."""
    return render(request, "halloween/sliding_puzzle.html")
