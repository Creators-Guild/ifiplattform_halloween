from django.conf import settings


def umami(request):
    return {
        "UMAMI_SCRIPT_URL": settings.UMAMI_SCRIPT_URL,
        "UMAMI_WEBSITE_ID": settings.UMAMI_WEBSITE_ID,
    }
