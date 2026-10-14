"""Stereotypical student jokes for the study section's "under development"
page -- one is picked at random on every visit (see
templates/core/study_under_development.html)."""

from django.utils.translation import gettext_lazy as _

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
