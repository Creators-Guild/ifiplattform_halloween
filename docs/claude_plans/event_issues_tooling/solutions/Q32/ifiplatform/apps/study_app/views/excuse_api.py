"""GET /study/api/excuse/: a random study excuse as JSON, so the joke page
can show a new one without reloading. ?not=<text> leaves out the one on
the page now, so you never get the same one twice in a row."""

import random

from django.http import JsonResponse

from ..jokes import all_jokes


def excuse_api_view(request):
    jokes = [str(joke) for joke in all_jokes()]
    current = request.GET.get("not", "")
    choices = [joke for joke in jokes if joke != current] or jokes
    return JsonResponse({"joke": random.choice(choices), "count": len(jokes)})
