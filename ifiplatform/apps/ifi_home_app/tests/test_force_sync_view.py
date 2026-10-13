# pylint: disable=C0114,C0115,C0116
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


@mock.patch("ifi_home_app.views.event_views.call_command")
class ForceSyncRedirectTests(TestCase):
    """The "Sync Peoply now" button redirects back to `next`, but only to a
    URL on this site."""

    def setUp(self):
        staff = get_user_model().objects.create_user(
            username="staff", password="pw", is_staff=True
        )
        self.client.force_login(staff)
        self.url = reverse("force_sync_peoply_events")

    def test_redirects_to_local_next(self, call_command):
        response = self.client.post(self.url, {"next": "/nb/arrangementer/"})

        self.assertRedirects(
            response, "/nb/arrangementer/", fetch_redirect_response=False
        )
        call_command.assert_called_once_with("sync_peoply_events")

    def test_ignores_external_next(self, _call_command):
        response = self.client.post(self.url, {"next": "https://evil.example/"})

        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_missing_next_goes_home(self, _call_command):
        response = self.client.post(self.url)

        self.assertRedirects(response, "/", fetch_redirect_response=False)
