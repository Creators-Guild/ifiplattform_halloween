"""Norwegian Bokmaal -> English term pairs DeepL must translate exactly this
way (or not translate at all -- source == target means "leave as-is"), e.g.
proper nouns (tool names, student union names) DeepL otherwise tends to
guess-translate. Pushed to a DeepL glossary by
`manage.py sync_deepl_glossary` -- see that command's docstring for the full
setup. Edit this list and re-run the command whenever a new word needs
locking down; no code changes needed beyond that.

Keys/values are matched by DeepL as exact substrings, so keep them as the
specific proper noun (e.g. "Fadderuke") rather than a whole sentence."""

GLOSSARY_TERMS = {
    # IFI-tools named in README.md -- proper nouns, never translate.
    "Peoply": "Peoply",
    "Trix": "Trix",
    "IFI Rom": "IFI Rom",
    # Recurring event name (see ifi_home_app/management/commands/
    # seed_dev_data.py) -- a Norwegian term kept as-is in the English UI
    # rather than translated (e.g. NOT "Godparent week").
    "Fadderuke": "Orientation Week",
    "Fadder": "Buddy",
    "Fadderbarn": "Buddychild",  # please find a better translation ahah
    "fadderbarna": "buddychildren",
    "Fadderstyret": "The Buddy Council(Fadderstyret)",
    "dagen@ifi": "dagen@ifi",
    "Dagen@ifi": "Dagen@ifi",
    "pub crawl": "pub til pub",
    "worky": "worky",
    # Student union / linjeforening names -- proper nouns DeepL otherwise
    # tends to guess-translate. Homepage widget unions (see
    # ifi_home_app/dummydata/dummy_studentunions_objects.py):
    "ProgSys": "ProgSys",
    "PiTCH": "PiTCH",
    "IFI Rastløs": "IFI Rastløs",
    "Ifi Pitbulls": "Ifi Pitbulls",
    # Fadderuke sub-event host unions (see ifi_home_app/management/
    # seed_dev_data/constants.py's FADDERUKE_UNION_SPECS):
    "CYB": "CYB",
    "FUI": "FUI",
    "Progsys": "Progsys",
    "MAKI": "MAKI",
    "MA:KI": "MA:KI",
    "VIFI": "VIFI",
    "FU": "FU",
    "Mikro": "Mikro",
    "Defi": "Defi",
    "Sonen": "Sonen",
    "FIFI": "FIFI",
    "Digitus": "Digitus",
    "Navet": "Navet",
    # The guild that builds/maintains IfiPlatform itself (see
    # templates/partials/footer.html and partials/sidemenu/sidemenu.html) --
    # renamed from "Ifi-Guild of Creators".
    "Ifi-Creators' Guild": "Ifi-Creators' Guild",
    "pub til pub": "pub crawl",
    "bar til bar": "bar crawl",
    "guildmaster": "guildmaster",
    "generalforsamling": "general meeting",
    "studentforening": "student union",
}
