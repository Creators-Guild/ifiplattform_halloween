"""The GitHub-username form on the Commits page."""

from django import forms
from django.core.validators import RegexValidator
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from .models import GitHubLink

# GitHub's own rule: letters, digits and single hyphens between them, 1-39 long.
github_login_validator = RegexValidator(
    r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$",
    _("That isn't a valid GitHub username."),
)

TAKEN = _("That GitHub username is already linked to another account.")


class GitHubLinkForm(forms.Form):
    github_login = forms.CharField(
        label=_("Your GitHub username"),
        max_length=39,
        required=False,
        validators=[github_login_validator],
        help_text=_("Leave empty and save to unlink."),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_github_login(self):
        login = self.cleaned_data["github_login"].strip().lower()
        taken = (
            GitHubLink.objects.filter(github_login=login)
            .exclude(user=self.user)
            .exists()
        )
        if login and taken:
            raise forms.ValidationError(TAKEN)
        return login

    def save(self):
        """False when someone linked the same username between the check in
        clean_github_login and now (the unique column catches it)."""
        login = self.cleaned_data["github_login"]
        if not login:
            GitHubLink.objects.filter(user=self.user).delete()
            return True
        try:
            GitHubLink.objects.update_or_create(
                user=self.user, defaults={"github_login": login}
            )
        except IntegrityError:
            self.add_error("github_login", TAKEN)
            return False
        return True
