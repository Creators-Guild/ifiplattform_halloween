"""Views for the user's profile page."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required()
def main_view(request):
    """Display the main your-page view showing current user profile."""
    user = request.user  # get current user
    return render(
        request=request, template_name="core/yourpage_main.html", context={"user": user}
    )
