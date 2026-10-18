"""Helpers for the fortune teller (views/fortune.py)."""

import unicodedata


def clean_name(name):
    """ "  Kari " -> "kari", "Åse" -> "ase": lowercase ASCII letters only, so
    every way of typing a name gets the same fortune."""
    name = name.strip().lower()
    for letter, plain in (("æ", "ae"), ("ø", "o"), ("å", "a")):
        name = name.replace(letter, plain)
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
