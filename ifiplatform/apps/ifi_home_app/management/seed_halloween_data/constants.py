"""Pure data used by the seed_halloween_data command -- specs for the
Halloween content, and the nb -> en tables. The unions and menus are the
dev seed's own, so their English comes from seed_dev_data's tables."""

from ifi_home_app.management.seed_dev_data import constants as dev

CATEGORY_SPECS = dev.CATEGORY_SPECS
SEED_IMAGE_PATH = dev.SEED_IMAGE_PATH
SEED_IMAGE_TITLE = dev.SEED_IMAGE_TITLE

# Category title -> (title, intro, body heading, body paragraph), one
# article per CATEGORY_SPECS entry.
ARTICLE_SPECS = {
    "Praktisk": (
        "Kostyme på studentbudsjett",
        "Slik lager du et skummelt kostyme uten å tømme studielånet.",
        "Det du trenger",
        "Et gammelt laken, en saks og litt fantasi kommer deg langt.",
    ),
    "Akademisk": (
        "De skumleste bugsene i informatikkens historie",
        "Feil i koden som fortsatt gir utviklere mareritt.",
        "Uendelige løkker og andre monstre",
        "Noen bugs er så skumle at de bare dukker opp når ingen ser på.",
    ),
    "Sosialt": (
        "Halloweenfest på Ifi",
        "Kostymer, gresskar og godteri i kjelleren.",
        "Hva skjer?",
        "Ta med kostymet ditt og bli med på årets skumleste fest.",
    ),
    "Hjelp": (
        "Hjelp, det spøker i terminalen!",
        "Hva du gjør når terminalen begynner å oppføre seg rart.",
        "Ikke få panikk",
        "Start med å lese feilmeldingen. Den er sjelden så skummel som den ser ut.",
    ),
    "IfiPlattform": (
        "Om Halloween-utgaven av Ifi Plattform",
        "Denne siden er en lekeplass for commit-arrangementet.",
        "Fyll den med innhold",
        "Siden er nesten tom med vilje. Legg til artikler, arrangementer og "
        "design, og gjør den til årets skumleste nettside.",
    ),
}

# (title, intro, body heading, body paragraph, days before today)
NEWS_SPECS = [
    (
        "Gresskarene har landet på Ifi",
        "Hundre gresskar ble levert til Ifi i dag morges.",
        "Hvor kom de fra?",
        "Ingen vet hvem som bestilte dem, men de står nå i resepsjonen.",
        1,
    ),
    (
        "Spøkelse observert i Ole-Johan Dahls hus",
        "Flere studenter melder om et spøkelse på lesesalen.",
        "Vitner forteller",
        "Spøkelset skal ha sett ut som en student som aldri ble ferdig med masteren.",
        2,
    ),
]

# (title, event_type, days before Halloween, "HH:MM" or None)
EVENT_SPECS = [
    ("Frist for kostymekonkurranse", "deadline", 5, None),
    ("Gresskarskjæring", "social", 3, "17:00"),
    ("Halloweenfest", "social", 0, "19:00"),
]
EVENT_LOCATION = "Ole-Johan Dahls hus"

TOOL_SPEC = {
    "title": "Gresskar-generator",
    "description": "Et verktøy som lager et tilfeldig gresskar-ansikt.",
}

NEW_STUDENT_ARTICLE_SPEC = (
    "Overlevelsesguide for nye Ifi-studenter",
    "Alt du trenger for å overleve ditt første Halloween på Ifi.",
    "Første regel",
    "Aldri gå alene inn i kjelleren etter mørkets frembrudd.",
)

BANNER_TEXT = "Velkommen til Halloween-utgaven av Ifi Plattform 🎃"

BOARD_MESSAGE_SPECS = [
    {
        "title": "Velkommen!",
        "sender_name": "Seed script",
        "display_seconds": 30,
        "body": "<p>Denne siden er din å bygge. Lykke til, og god Halloween!</p>",
    },
]

TRANSLATIONS = {
    **dev.TRANSLATIONS,
    # ARTICLE_SPECS
    "Kostyme på studentbudsjett": "Costumes on a student budget",
    "Slik lager du et skummelt kostyme uten å tømme studielånet.": "How to make a scary costume without emptying your student loan.",
    "Det du trenger": "What you need",
    "Et gammelt laken, en saks og litt fantasi kommer deg langt.": "An old sheet, a pair of scissors and some imagination go a long way.",
    "De skumleste bugsene i informatikkens historie": "The scariest bugs in computing history",
    "Feil i koden som fortsatt gir utviklere mareritt.": "Bugs that still give developers nightmares.",
    "Uendelige løkker og andre monstre": "Infinite loops and other monsters",
    "Noen bugs er så skumle at de bare dukker opp når ingen ser på.": "Some bugs are so scary they only show up when nobody is looking.",
    "Halloweenfest på Ifi": "Halloween party at Ifi",
    "Kostymer, gresskar og godteri i kjelleren.": "Costumes, pumpkins and candy in the basement.",
    "Hva skjer?": "What's happening?",
    "Ta med kostymet ditt og bli med på årets skumleste fest.": "Bring your costume and join the scariest party of the year.",
    "Hjelp, det spøker i terminalen!": "Help, my terminal is haunted!",
    "Hva du gjør når terminalen begynner å oppføre seg rart.": "What to do when your terminal starts acting strange.",
    "Ikke få panikk": "Don't panic",
    "Start med å lese feilmeldingen. Den er sjelden så skummel som den ser ut.": "Start by reading the error message. It's rarely as scary as it looks.",
    "Om Halloween-utgaven av Ifi Plattform": "About the Halloween edition of Ifi Platform",
    "Denne siden er en lekeplass for commit-arrangementet.": "This site is a playground for the commit event.",
    "Fyll den med innhold": "Fill it with content",
    "Siden er nesten tom med vilje. Legg til artikler, arrangementer og design, og gjør den til årets skumleste nettside.": "The site is almost empty on purpose. Add articles, events and design, and make it the scariest website of the year.",
    # NEWS_SPECS
    "Gresskarene har landet på Ifi": "The pumpkins have landed at Ifi",
    "Hundre gresskar ble levert til Ifi i dag morges.": "A hundred pumpkins were delivered to Ifi this morning.",
    "Hvor kom de fra?": "Where did they come from?",
    "Ingen vet hvem som bestilte dem, men de står nå i resepsjonen.": "Nobody knows who ordered them, but they are now in the reception.",
    "Spøkelse observert i Ole-Johan Dahls hus": "Ghost spotted in Ole-Johan Dahl's House",
    "Flere studenter melder om et spøkelse på lesesalen.": "Several students report a ghost in the reading room.",
    "Vitner forteller": "Witnesses speak",
    "Spøkelset skal ha sett ut som en student som aldri ble ferdig med masteren.": "The ghost reportedly looked like a student who never finished their master's.",
    # EVENT_SPECS
    "Frist for kostymekonkurranse": "Deadline: costume contest",
    "Gresskarskjæring": "Pumpkin carving",
    "Halloweenfest": "Halloween party",
    # TOOL_SPEC
    "Gresskar-generator": "Pumpkin generator",
    "Et verktøy som lager et tilfeldig gresskar-ansikt.": "A tool that makes a random pumpkin face.",
    # NEW_STUDENT_ARTICLE_SPEC
    "Overlevelsesguide for nye Ifi-studenter": "Survival guide for new Ifi students",
    "Alt du trenger for å overleve ditt første Halloween på Ifi.": "Everything you need to survive your first Halloween at Ifi.",
    "Første regel": "Rule number one",
    "Aldri gå alene inn i kjelleren etter mørkets frembrudd.": "Never go into the basement alone after dark.",
    # Messages
    BANNER_TEXT: "Welcome to the Halloween edition of Ifi Platform 🎃",
    "Velkommen!": "Welcome!",
    "Denne siden er din å bygge. Lykke til, og god Halloween!": "This site is yours to build. Good luck, and happy Halloween!",
}

SAME_IN_ENGLISH = dev.SAME_IN_ENGLISH | {EVENT_LOCATION}
