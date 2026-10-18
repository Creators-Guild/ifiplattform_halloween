"""The Ifi Halloween quiz in the Halloween corner: ten questions, and a
score at the end."""

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
    {
        "key": "q3",
        "question": "Which date is Halloween?",
        "options": ["31 October", "1 November", "13 October"],
        "answer": "31 October",
    },
    {
        "key": "q4",
        "question": "What does print(2 ** 3) show in Python?",
        "options": ["8", "6", "23"],
        "answer": "8",
    },
    {
        "key": "q5",
        "question": "Simula is known as the first language with...",
        "options": ["objects and classes", "emojis", "automatic semicolons"],
        "answer": "objects and classes",
    },
    {
        "key": "q6",
        "question": "Which git command saves your changes as a new version?",
        "options": ["git commit", "git haunt", "git save"],
        "answer": "git commit",
    },
    {
        "key": "q7",
        "question": "What do vampires famously avoid?",
        "options": ["Garlic", "Coffee", "Semicolons"],
        "answer": "Garlic",
    },
    {
        "key": "q8",
        "question": "Which HTTP status code means \"page not found\"?",
        "options": ["404", "200", "500"],
        "answer": "404",
    },
    {
        "key": "q9",
        "question": "Kristen Nygaard, who the other Ifi building is named after, worked with...",
        "options": ["Ole-Johan Dahl", "Count Dracula", "Ada Lovelace"],
        "answer": "Ole-Johan Dahl",
    },
    {
        "key": "q10",
        "question": "What is a bug in a program?",
        "options": ["A mistake", "A small spider", "A new feature"],
        "answer": "A mistake",
    },
]


def score(answers):
    """answers: question key -> the option the visitor picked (or None).
    Returns how many are right."""
    return sum(1 for question in QUESTIONS if answers.get(question["key"]) == question["answer"])


def verdict(points, total):
    """A sentence about the score."""
    if points == total:
        return "Perfect! The ghosts bow to you."
    if points >= total / 2:
        return "Not bad. The pumpkins are impressed."
    return "Oh no. Even the bats are disappointed."


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
