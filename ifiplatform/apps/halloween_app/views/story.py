"""The haunted story in the Halloween corner: fill in the blanks, get a
story. Half built: the form works, the story is the event issue's job (the
TODOs)."""

from django.shortcuts import render

FIELDS = [
    ("name", "A name"),
    ("place", "A place at Ifi"),
    ("food", "A food"),
    ("number", "A number"),
    ("creature", "A creature"),
    ("sound", "A sound"),
]


def tell_story(words):
    """words: every field's key -> what the visitor typed. Returns the story
    as a list of paragraphs, or None if a word is missing."""
    # TODO 1: if any word is empty, return None.
    # TODO 2: write the story: at least 3 paragraphs (strings), using every
    # word at least once.
    return None


def story_view(request):
    words = {key: request.GET.get(key, "").strip() for key, _label in FIELDS}
    told = "tell" in request.GET
    story = tell_story(words) if told else None
    return render(
        request,
        "halloween/story.html",
        {"fields": [(key, label, words[key]) for key, label in FIELDS], "told": told, "story": story},
    )
