"""GET /study/api/excuse/: a random study excuse as JSON, so the joke page
can show a new one without reloading. Not built yet: that's an event issue."""

from django.http import JsonResponse


def excuse_api_view(request):
    return JsonResponse({"error": "Not built yet"}, status=501)
