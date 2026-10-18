# pylint: disable=C0114,C0115,C0116
from django.test import SimpleTestCase

from halloween_app.views.quiz import QUESTIONS, score, verdict


class QuizTests(SimpleTestCase):
    def test_ten_questions_with_different_keys(self):
        self.assertEqual(len(QUESTIONS), 10)
        self.assertEqual(len({question["key"] for question in QUESTIONS}), 10)

    def test_every_answer_is_an_option(self):
        for question in QUESTIONS:
            self.assertIn(question["answer"], question["options"], question["key"])

    def test_all_right(self):
        answers = {question["key"]: question["answer"] for question in QUESTIONS}
        self.assertEqual(score(answers), 10)

    def test_nothing_answered(self):
        self.assertEqual(score({}), 0)

    def test_verdicts_differ(self):
        self.assertEqual(len({verdict(0, 10), verdict(5, 10), verdict(10, 10)}), 3)
