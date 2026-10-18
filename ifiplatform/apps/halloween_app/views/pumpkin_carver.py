# pylint: disable=C0114
from django.shortcuts import render


def pumpkin_carver_view(request):
    """The pumpkin carver: carving it is static/js/halloween_pages/pumpkin_carver.js."""
    return render(request, "halloween/pumpkin_carver.html")
