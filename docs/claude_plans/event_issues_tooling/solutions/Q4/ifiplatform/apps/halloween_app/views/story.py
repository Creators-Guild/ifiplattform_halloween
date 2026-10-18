"""The haunted story in the Halloween corner: fill in the blanks, get a
story."""

from django.shortcuts import render

FIELDS = [
    ("name", "A name"),
    ("place", "A place at Ifi"),
    ("food", "A food"),
    ("number", "A number"),
    ("creature", "A creature"),
    ("sound", "A sound"),
]

STORY = [
    "It was a dark and stormy night at Ifi. {name} was the last one left in {place}, "
    "eating cold {food} and fixing one last bug.",
    "At exactly {number} minutes past midnight, the lights flickered. Somewhere down the "
    "corridor came a sound: \"{sound}!\"",
    "{name} turned around slowly. There, holding a laptop, stood a {creature}. "
    "\"Your tests are failing,\" it whispered, and reached for the {food}.",
    "Nobody knows what happened next. But to this day, if you sit in {place} after "
    "midnight, you can still hear it: \"{sound}...\"",
]


def tell_story(words):
    """words: every field's key -> what the visitor typed. Returns the story
    as a list of paragraphs, or None if a word is missing."""
    if not all(words.get(key) for key, _label in FIELDS):
        return None
    return [paragraph.format(**words) for paragraph in STORY]


def story_view(request):
    words = {key: request.GET.get(key, "").strip() for key, _label in FIELDS}
    told = "tell" in request.GET
    story = tell_story(words) if told else None
    return render(
        request,
        "halloween/story.html",
        {"fields": [(key, label, words[key]) for key, label in FIELDS], "told": told, "story": story},
    )
