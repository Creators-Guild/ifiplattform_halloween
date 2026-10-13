"""Views for multiple choice quiz feature."""

from django.shortcuts import render


def menu_view(request):
    """Display the multiple choice quiz menu."""
    return render(request, "multiplechoice/core/menu.html")
