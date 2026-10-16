# pylint: disable=C0114
from django.shortcuts import render

from ..board import load_notes


def board_view(request):
    """The haunted notice board: every note in board_notes/."""
    return render(request, "halloween/board.html", {"notes": load_notes()})
