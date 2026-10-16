# pylint: disable=C0114
from django.shortcuts import render


def preview_404_view(request):
    """templates/404.html, also while DEBUG is on (then Django shows its own
    debug page for real 404s)."""
    return render(request, "404.html", status=404)
