"""Helpers for the fortune teller (views/fortune.py)."""


def clean_name(name):
    """ "  Kari " -> "kari": lowercase letters only, so every way of typing a
    name gets the same fortune."""
    name = name.strip().lower()
    return name.encode("ascii").decode()
