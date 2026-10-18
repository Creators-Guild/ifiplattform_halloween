# pylint: disable=C0114
from django.shortcuts import render


def memory_view(request):
    """Memory pairs: the game itself is static/js/halloween_pages/memory.js."""
    return render(request, "halloween/memory.html")
