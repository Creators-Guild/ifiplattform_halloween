from django.conf import settings


def umami(request):
    return {
        "UMAMI_SCRIPT_URL": settings.UMAMI_SCRIPT_URL,
        "UMAMI_WEBSITE_ID": settings.UMAMI_WEBSITE_ID,
    }


def open_signup(request):
    return {"OPEN_SIGNUP": settings.OPEN_SIGNUP}
