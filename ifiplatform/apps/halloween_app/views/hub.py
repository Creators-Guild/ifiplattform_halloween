# pylint: disable=C0114
from django.shortcuts import render

from ..hub import hub_pages


def hub_view(request):
    """The Halloween corner's front page: a card for every page."""
    return render(request, "halloween/hub.html", {"pages": hub_pages()})
