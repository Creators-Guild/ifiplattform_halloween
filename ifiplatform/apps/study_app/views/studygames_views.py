"""Views for study games feature."""

from django.shortcuts import render


def menu_view(request):
    """Display the study games menu."""
    return render(request, "studygames/core/menu.html")
