"""Custom user registration form."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from account_app.models import Profile


class SignupForm(UserCreationForm):
    """Registration form requiring username, email, first and last name (in
    addition to UserCreationForm's own username/password1/password2), with a
    uniqueness check on email since it's also how a user would be looked up
    for email verification/password reset."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["username", "email", "first_name", "last_name"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ResendVerificationForm(forms.Form):
    """Just an email address -- the view looks up the matching inactive
    account (if any) itself, see resend_verification_view."""

    email = forms.EmailField(required=True)


class ProfileForm(forms.ModelForm):
    """Lets an existing user fill in/update email, first and last name from
    their account settings page. All optional (unlike SignupForm) -- this is
    a nudge for accounts that predate those becoming required at signup, not
    something existing users are forced to complete.

    Once a field has a value, a regular user can no longer blank it back out
    (only fill it in or change it) -- pass allow_clearing=True (staff/admins
    editing an account) to lift that restriction."""

    def __init__(self, *args, allow_clearing=False, **kwargs):
        self.allow_clearing = allow_clearing
        super().__init__(*args, **kwargs)
        # locked by default -- profile_edit_toggle.js removes this when the
        # matching "Edit" link is clicked. readonly (not disabled) so the
        # current value still submits as-is if left untouched.
        for field in self.fields.values():
            field.widget.attrs["readonly"] = True
            field.widget.attrs["class"] = "field-locked"

    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name"]

    def _reject_blanking(self, field_name):
        value = self.cleaned_data.get(field_name, "")
        had_value_before = bool(getattr(self.instance, field_name, ""))
        if had_value_before and not value and not self.allow_clearing:
            raise forms.ValidationError("This field can't be cleared once set.")
        return value

    def clean_email(self):
        email = self._reject_blanking("email")
        if (
            email
            and get_user_model()
            .objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_first_name(self):
        return self._reject_blanking("first_name")

    def clean_last_name(self):
        return self._reject_blanking("last_name")


class NicknameForm(forms.ModelForm):
    """Lets a user set/change the optional nickname on their Profile,
    used instead of their real name on content they choose to attribute
    that way -- see ArticlePage.author_attribution."""

    class Meta:
        model = Profile
        fields = ["nickname"]


class AccountDeleteForm(forms.Form):
    """Confirms self-service account deletion -- see delete_account_view.
    Requires the current password (re-auth: CSRF alone doesn't stop a
    hijacked session or shared/unlocked browser from triggering an
    irreversible action, and there's no 2FA backstop in this app), plus two
    independent choices for what happens to the user's own content:
    study tools (decks/flashcards) can be deleted outright or kept, and
    articles/news -- never deleted, they're platform/union property -- are
    always credited one of three ways once the account is gone."""

    ATTRIBUTION_CHOICES = [
        ("real_name", "My real name"),
        ("nickname", "My nickname"),
        ("unknown", "Unknown (anonymous)"),
    ]

    password = forms.CharField(widget=forms.PasswordInput)
    study_tools_action = forms.ChoiceField(
        choices=[("delete", "Delete them"), ("keep", "Keep them")],
        widget=forms.RadioSelect,
    )
    study_tools_attribution = forms.ChoiceField(
        choices=ATTRIBUTION_CHOICES, widget=forms.RadioSelect, required=False
    )
    articles_attribution = forms.ChoiceField(
        choices=ATTRIBUTION_CHOICES, widget=forms.RadioSelect
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        nickname = getattr(getattr(self.user, "profile", None), "nickname", "")
        wants_nickname = "nickname" in (
            cleaned_data.get("articles_attribution"),
            (
                cleaned_data.get("study_tools_attribution")
                if cleaned_data.get("study_tools_action") == "keep"
                else None
            ),
        )
        if wants_nickname and not nickname:
            raise forms.ValidationError(
                "Set a nickname in your account settings before choosing to "
                "be credited by nickname."
            )
        return cleaned_data
