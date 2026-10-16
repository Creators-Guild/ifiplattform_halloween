"""The pages of the Halloween corner, in the order the hub shows them. Each
slug has a view in views/<slug>.py, a template in templates/halloween/ and a
stylesheet in static/css/halloween_pages/. Owned by the organisers: issues
fill in the pages, they don't add them here."""

PAGES = [
    ("board", "📌", "Haunted notice board", "Obituaries, warnings, rules and missing posters, pinned by everyone."),
    ("fortune", "🔮", "Fortune teller", "Tell the crystal ball your name."),
    ("spooky_name", "🧛", "Spooky name generator", "Find out what your name is after dark."),
    ("potion", "🧪", "Potion mixer", "Pick your ingredients and see what you brewed."),
    ("whack_a_bat", "🦇", "Whack-a-bat", "Hit the bats before they fly off."),
    ("memory", "🃏", "Memory pairs", "Find the matching Halloween pairs."),
]
