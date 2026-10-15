"""The admin's Users pages (/admin/users/) with email, first name and last
name optional. Wagtail requires them by default, but accounts made through
the open sign-up only have a username and password, so the admin couldn't
save them. Wired in by OptionalNamesUsersAppConfig (apps.py), which takes
the place of "wagtail.users" in INSTALLED_APPS."""

from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.views.users import UserViewSet as WagtailUserViewSet


class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, label=_("Email"))
    first_name = forms.CharField(required=False, label=_("First Name"))
    last_name = forms.CharField(required=False, label=_("Last Name"))


class AdminUserEditForm(UserEditForm):
    email = forms.EmailField(required=False, label=_("Email"))
    first_name = forms.CharField(required=False, label=_("First Name"))
    last_name = forms.CharField(required=False, label=_("Last Name"))


class UserViewSet(WagtailUserViewSet):
    def get_form_class(self, for_update=False):
        return AdminUserEditForm if for_update else AdminUserCreationForm
