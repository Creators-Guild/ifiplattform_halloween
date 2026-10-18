"""The Ifi Halloween quiz in the Halloween corner. Half built: the page
shows the questions, more questions and the score are the event issue's job
(the TODOs)."""

from django.shortcuts import render

QUESTIONS = [
    {
        "key": "q1",
        "question": "Ole-Johan Dahl, who the Ifi building is named after, co-created...",
        "options": ["the programming language Simula", "the first pumpkin computer", "the web browser"],
        "answer": "the programming language Simula",
    },
    {
        "key": "q2",
        "question": "What is a carved pumpkin with a candle inside called?",
        "options": ["A jack-o'-lantern", "A pumpkin pie", "A gourd light"],
        "answer": "A jack-o'-lantern",
    },
    # TODO 1: add 8 more questions (10 in all), about Ifi, programming or
    # Halloween. Every key must be different.
]


def score(answers):
    """answers: question key -> the option the visitor picked (or None).
    Returns how many are right."""
    # TODO 2: count the right answers.
    return 0


def verdict(points, total):
    """A sentence about the score, for example "3/10: the ghosts are
    disappointed"."""
    # TODO 3: a different sentence for a low, a middle and a full score.
    return None


def quiz_view(request):
    answers = {question["key"]: request.GET.get(question["key"]) for question in QUESTIONS}
    checked = "check" in request.GET
    points = score(answers) if checked else None
    return render(
        request,
        "halloween/quiz.html",
        {
            "questions": [{**question, "picked": answers[question["key"]]} for question in QUESTIONS],
            "checked": checked,
            "points": points,
            "total": len(QUESTIONS),
            "verdict": verdict(points, len(QUESTIONS)) if checked else None,
        },
    )
