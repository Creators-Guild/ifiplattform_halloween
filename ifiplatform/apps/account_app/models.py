from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Small per-user extension to Django's stock User model, for state that
    doesn't belong on User itself and doesn't warrant a full custom user
    model (AUTH_USER_MODEL swap). Tracks an in-progress email change, an
    optional nickname (used instead of the real name on content the user
    chooses to attribute that way -- see ArticlePage.author_attribution),
    and whether the user has responded to the editor content-ownership
    terms -- see account_app/views/account_views.py."""

    EDITOR_TERMS_CHOICES = [
        ("pending", "Pending"),
        ("agreed", "Agreed"),
        ("disagreed", "Disagreed"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    pending_email = models.EmailField(
        blank=True,
        help_text="A new email address awaiting confirmation, if any -- see confirm_email_change_view.",
    )
    nickname = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional -- lets this user be credited on content without using their real name.",
    )
    editor_terms_status = models.CharField(
        max_length=10,
        choices=EDITOR_TERMS_CHOICES,
        default="pending",
        help_text=(
            "Whether this user has responded to the content-ownership terms "
            "shown once they're granted permission to write pages -- see "
            "account_settings_view's show_editor_notice. Re-checked against "
            "live permission state on every account settings page load "
            "(not just set once), so this naturally resets to relevant "
            "again if the notice needs to reappear."
        ),
    )

    def __str__(self):
        return f"Profile({self.user})"
