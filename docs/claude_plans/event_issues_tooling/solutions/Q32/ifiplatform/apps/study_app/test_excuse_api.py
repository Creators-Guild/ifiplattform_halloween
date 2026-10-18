"""The study page's excuse API (views/excuse_api.py)."""

# pylint: disable=C0115,C0116
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from study_app.jokes import all_jokes


class ExcuseApiTests(TestCase):
    def setUp(self):
        self.enterContext(translation.override("en"))

    def test_gives_one_of_the_jokes(self):
        response = self.client.get(reverse("study_excuse_api"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["joke"], [str(joke) for joke in all_jokes()])

    def test_never_the_same_twice_in_a_row(self):
        current = str(all_jokes()[0])
        for _ in range(30):
            response = self.client.get(reverse("study_excuse_api"), {"not": current})
            self.assertNotEqual(response.json()["joke"], current)

    def test_unknown_not_is_fine(self):
        self.assertEqual(self.client.get(reverse("study_excuse_api"), {"not": "nonsense"}).status_code, 200)
