"""The costume of the day on the Halloween corner's front page: the same
costume all day, for everyone, and a new one tomorrow."""

import random

COSTUMES = [
    ("🧛", "A vampire who only drinks cold coffee"),
    ("🧟", "A zombie TA, still grading"),
    ("👻", "The ghost of a deleted branch"),
    ("🧙", "A witch with a very long stack trace"),
    ("🎃", "A pumpkin that runs on Linux"),
    ("🦇", "A bat that only flies at night (like your deadlines)"),
    ("💀", "A skeleton made of leftover semicolons"),
    ("🕷️", "A spider that writes the World Wide Web"),
]


def costume_of_the_day(day):
    """day: a date. The same date always gives the same (emoji, costume)."""
    return random.Random(day.toordinal()).choice(COSTUMES)
