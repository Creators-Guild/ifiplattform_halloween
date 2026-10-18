"""Stereotypical student jokes for the study section's "under development"
page -- one is picked at random on every visit (see
templates/core/study_under_development.html). STUDY_JOKES are translated;
the files in joke_files/ (one joke each, added by Commit for Candy issues)
show as written, in any language."""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

JOKE_FILES_DIR = Path(__file__).parent / "joke_files"

STUDY_JOKES = [
    _(
        "Step 1: open the textbook. Step 2: check your phone. "
        "Step 3: it's 3 a.m. and the exam is tomorrow."
    ),
    _(
        "I'll start studying right after this one episode. "
        "(Every student, six episodes ago.)"
    ),
    _("My study plan: panic. My backup plan: also panic."),
    _("Ctrl+C and Ctrl+V got me through IN1000. Ctrl+Z is getting me through life."),
    _(
        'The course page says "about 10 hours a week". '
        "The course page has never met me."
    ),
    _("Group study: one person studies, three people discuss " "where to get lunch."),
    _("I don't procrastinate. I wait for the deadline to motivate me."),
    _("Exam tomorrow? Perfect time to reorganise my entire desk."),
    _("I understood the lecture. Then the lecturer moved on to the second slide."),
    _("Real programmers learn from the docs. I learn from the error messages."),
    _("It worked on my machine. My machine isn't taking the exam."),
    _("Coffee isn't a drink, it's a study method."),
]


def file_jokes():
    """The text of every joke_*.txt in joke_files/, read on every call so a
    new file shows without a restart. Empty or unreadable files are skipped."""
    jokes = []
    for path in sorted(JOKE_FILES_DIR.glob("joke_*.txt")):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            continue
        if text:
            jokes.append(text)
    return jokes


def file_joke(number):
    """The joke in joke_<number>.txt ("05" or "5"), or None."""
    if not str(number).isdigit():
        return None
    path = JOKE_FILES_DIR / f"joke_{int(number):02d}.txt"
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeDecodeError):
        return None


def all_jokes():
    """STUDY_JOKES and the joke files together."""
    return [*STUDY_JOKES, *file_jokes()]
