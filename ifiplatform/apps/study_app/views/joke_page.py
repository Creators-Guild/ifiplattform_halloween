"""The study section's joke page, shown for every /study/ path while the
section is under development. ?joke=05 shows joke_files/joke_05.txt, so
whoever wrote it can find it; otherwise a random joke."""

import random

from django.shortcuts import render
from django.utils.translation import gettext as _

from ..jokes import all_jokes, file_joke


def joke_page_view(request):
    joke = file_joke(request.GET.get("joke", "")) or random.choice(all_jokes())
    return render(request, "core/study_under_development.html", {"app_name": _("Study"), "joke": joke})
