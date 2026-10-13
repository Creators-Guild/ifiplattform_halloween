"""Views for the study app main menu."""

from django.shortcuts import render


def main_view(request):
    """Display the main study app menu page."""
    return render(request=request, template_name="core/study_main.html")
