"""URL configuration for the account app."""

from django.urls import path
from .views import login_views
from .views import account_views
from .views import legal_views

urlpatterns = [
    path("privacy_policy", legal_views.privacy_policy_view, name="privacy_policy"),
    path("signin", login_views.signin_view, name="signin"),
    path("signin_success", login_views.signin_success_view, name="signin_success"),
    path(
        "verify_email_sent",
        login_views.verify_email_sent_view,
        name="verify_email_sent",
    ),
    path(
        "verify/<uidb64>/<token>/",
        login_views.verify_email_view,
        name="verify_email",
    ),
    path(
        "resend_verification",
        login_views.resend_verification_view,
        name="resend_verification",
    ),
    path("login", login_views.login_view, name="login"),
    path("logout", login_views.logout_view, name="logout"),
    path(
        "account_settings", account_views.account_settings_view, name="account_settings"
    ),
    path("update_nickname", account_views.update_nickname_view, name="update_nickname"),
    path(
        "editor_terms_response",
        account_views.editor_terms_response_view,
        name="editor_terms_response",
    ),
    path("export_data", account_views.export_data_view, name="export_data"),
    path("delete_account", account_views.delete_account_view, name="delete_account"),
    path(
        "email_change_sent",
        account_views.email_change_sent_view,
        name="email_change_sent",
    ),
    path(
        "confirm_email_change/<token>/",
        account_views.confirm_email_change_view,
        name="confirm_email_change",
    ),
    path(
        "cancel_email_change",
        account_views.cancel_email_change_view,
        name="cancel_email_change",
    ),
]
