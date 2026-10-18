"""The pages of the Halloween corner (hub.py decides the order the hub
shows them in). Each slug has a view in views/<slug>.py, a template in
templates/halloween/ and a stylesheet in static/css/halloween_pages/. Owned
by the organisers: issues fill in the pages, they don't add them here."""

PAGES = [
    ("board", "📌", "Haunted notice board", "Obituaries, warnings, rules and missing posters, pinned by everyone."),
    ("fortune", "🔮", "Fortune teller", "Tell the crystal ball your name."),
    ("spooky_name", "🧛", "Spooky name generator", "Find out what your name is after dark."),
    ("potion", "🧪", "Potion mixer", "Pick your ingredients and see what you brewed."),
    ("whack_a_bat", "🦇", "Whack-a-bat", "Hit the bats before they fly off."),
    ("memory", "🃏", "Memory pairs", "Find the matching Halloween pairs."),
    ("zombie_typing", "🧟", "Zombie typing", "Type the words before the zombies reach you."),
    ("sliding_puzzle", "🌕", "Moon puzzle", "Slide the pieces until the moon is whole again."),
    ("bat_snake", "🐍", "Bat snake", "A bat that grows with every candy it eats."),
    ("costume", "🎭", "Costume generator", "No costume yet? Roll one."),
    ("story", "📖", "Haunted story", "Fill in the blanks, get a spooky story."),
    ("quiz", "❓", "Halloween quiz", "Ten questions about Ifi and Halloween."),
    ("graveyard", "🪦", "Graveyard", "Features this site used to have. Rest in peace."),
    ("countdown", "⏳", "Countdown", "How long until Halloween?"),
    ("pumpkin_carver", "🔪", "Pumpkin carver", "Carve your own jack-o'-lantern."),
]
