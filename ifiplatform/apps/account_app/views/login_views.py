"""Views for handling user login, logout, and registration."""

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from account_app.forms import ResendVerificationForm, SignupForm


def _send_verification_email(request, user):
    """Email `user` a signup-confirmation link containing their uid + a
    single-use token (same mechanism Django's own password-reset flow uses:
    django.contrib.auth.tokens.default_token_generator)."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse("verify_email", kwargs={"uidb64": uidb64, "token": token})
    )
    message = render_to_string(
        "login/email/verification_email.txt",
        {"user": user, "verify_url": verify_url},
    )
    send_mail(
        subject="Confirm your Ifi Platform account",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    if settings.DEBUG:
        # the console backend dumps the raw MIME message, which soft-wraps
        # long lines (quoted-printable encoding) -- a real mail client
        # dequotes that transparently before you'd ever see/copy the link,
        # but reading it straight from this raw dump means the URL can come
        # out split mid-token if you copy it as printed. Print it again here,
        # plain and unwrapped, so local testing has something safe to copy.
        print(f"[verification email] {user.email} -> {verify_url}")


def signin_view(request):
    """Handle new user registration (username/email/first name/last name all
    required, see SignupForm). The account starts inactive -- Django's
    ModelBackend already refuses to authenticate an inactive user, so login
    stays blocked on its own until they click the emailed verification link."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            _send_verification_email(request, user)
            return redirect("verify_email_sent")
    else:  # if GET
        form = SignupForm()

    return render(
        request=request, template_name="login/signin.html", context={"form": form}
    )


def verify_email_sent_view(request):
    """Shown right after signup, telling the user to check their email."""
    return render(request=request, template_name="login/verify_email_sent.html")


def resend_verification_view(request):
    """Re-send the verification email for an account that's still inactive.
    Always shows the same confirmation regardless of whether a matching
    account was actually found/re-emailed -- otherwise the response itself
    would leak which email addresses are registered."""
    if request.method == "POST":
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            user = (
                get_user_model()
                .objects.filter(
                    email__iexact=form.cleaned_data["email"], is_active=False
                )
                .first()
            )
            if user is not None:
                _send_verification_email(request, user)
            return redirect("verify_email_sent")
    else:
        form = ResendVerificationForm()

    return render(
        request=request,
        template_name="login/resend_verification.html",
        context={"form": form},
    )


def verify_email_view(request, uidb64, token):
    """Activate a newly-registered account from the link in the
    verification email, then log them straight in."""
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if (
        user is not None
        and not user.is_active
        and default_token_generator.check_token(user, token)
    ):
        user.is_active = True
        user.save(update_fields=["is_active"])
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request=request, user=user)
        return render(
            request=request,
            template_name="login/verify_email_success.html",
            context={"user": user},
        )

    return render(request=request, template_name="login/verify_email_invalid.html")


def signin_success_view(request):
    """Render the registration success page for the newly created user."""
    user = request.user
    return render(
        request=request,
        template_name="login/signin_success.html",
        context={"user": user},
    )


def login_view(request):
    """Handle user login and redirect to next page or home after success."""
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request=request, user=user)

            # check if there was a page user
            # tried to access without being logged in
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)

            # else default redirecct
            return redirect("ifi_home")
    else:
        form = AuthenticationForm()

    return render(
        request=request, template_name="login/login.html", context={"form": form}
    )


def logout_view(request):
    """Log the current user out and render the logout confirmation page."""
    # logout() clears request.user to AnonymousUser in place, so grab the
    # name for the goodbye message before calling it, not after.
    display_name = (
        request.user.first_name or request.user.username
        if request.user.is_authenticated
        else ""
    )
    logout(request=request)

    return render(
        request=request,
        template_name="login/logout.html",
        context={"display_name": display_name},
    )
