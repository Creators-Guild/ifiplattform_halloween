# pylint: disable=C0114,C0115,C0116
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils import translation

from study_app.jokes import STUDY_JOKES


class StudyJokePageTests(TestCase):
    """While study_app is under development, every /study/ path shows the
    joke page with one of STUDY_JOKES."""

    def test_shows_a_joke_on_any_study_path(self):
        with translation.override("en"):
            for url in [reverse("study_home"), reverse("study_home") + "anything/"]:
                response = self.client.get(url)
                self.assertContains(response, "Ahaha, no.")
                self.assertTrue(
                    any(
                        escape(str(joke)) in response.content.decode()
                        for joke in STUDY_JOKES
                    )
                )
