"""Views for mixed study set feature."""

from django.shortcuts import render


def menu_view(request):
    """Display the mixed study set menu."""
    return render(request, "mix_studyset/core/menu.html")
