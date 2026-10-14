"""Who may see the helpers' solutions -- the one place that decides it, used
by the issue board, the issue page and their templates."""

HELPERS_GROUP = "Helpers"


def is_organiser(user):
    """Staff or superuser: may press the leaderboard's organiser buttons."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def can_see_solutions(user):
    """Organisers, and members of the Helpers group."""
    return is_organiser(user) or (
        user.is_authenticated and user.groups.filter(name=HELPERS_GROUP).exists()
    )
