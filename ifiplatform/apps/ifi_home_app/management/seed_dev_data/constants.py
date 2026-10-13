"""Pure data used by the seed_dev_data command's various mixins -- specs for
what to create, and the nb -> en translation table. No logic here."""

from pathlib import Path

from django.conf import settings
from wagtail.rich_text import RichText

SEED_IMAGE_PATH = (
    Path(settings.BASE_DIR)
    / "static"
    / "images"
    / "studentunions"
    / "IfiPitbullsLogo.jpg"
)
SEED_IMAGE_TITLE = "Dev seed placeholder image"

CATEGORY_SPECS = [
    ("Praktisk", "turq"),
    ("Akademisk", "pink"),
    ("Sosialt", "purple"),
    ("Hjelp", "turq"),
    ("IfiPlattform", "pink"),
]

# Deliberately long, wraps-onto-multiple-words name -- exercises the home
# nav's Student Unions dropdown at a length real union names can plausibly
# reach, to test dropdownmenu.css's max-width/wrapping on narrow screens.
# menus.py puts it in the Student Unions menu group so it actually appears there.
LONG_UNION_NAME = (
    "Den Ekstremt Lange Studentforeningen for Informatikkstudenter med "
    "Spesiell Interesse for Kunstig Intelligens og Maskinlæring"
)

NEWS_ARTICLE_TITLES = [
    "Nyhetsartikkel 1",
    "Nyhetsartikkel 2",
    "Nyhetsartikkel 3",
    "Nyhetsartikkel 4",
]

# (title, event_type, days-from-today for event_date, event_time or None,
# days-from-event_date for end_date or None) -- mirrors the "This month at
# Ifi" mockup: a week-long event with no fixed time (Fadderuke), a dated
# social with a time (Bar til bar), a deadline (Frist for funk-oppmelding),
# and a company presentation (DNB).
EVENT_SPECS = [
    ("Fadderuke", "social", 3, None, 4),
    ("Bar til bar", "social", 8, "17:00", None),
    ("Frist for funk-oppmelding for Dagen@IFI", "deadline", 12, None, None),
    ("DNB Bedriftspresentasjon med Navet", "company", 20, "16:00", None),
]

# Recurring "company presentation" EventPages for Navet, every Tuesday and
# Thursday for NAVET_COMPANY_PRESENTATION_WEEKS weeks -- Navet's real
# Peoply events were removed, so sync_peoply_events no longer produces any
# for it; this keeps its calendar looking realistic in local dev regardless
# (see EventSeedMixin._seed_navet_company_presentations). Company names
# just cycle through this list in order.
NAVET_COMPANY_PRESENTATION_COMPANIES = ["Bouvet", "Bekk", "Computas", "Sopra Steria"]
NAVET_COMPANY_PRESENTATION_WEEKS = 6
NAVET_COMPANY_PRESENTATION_TIME = "16:30"
NAVET_COMPANY_PRESENTATION_END_TIME = "18:30"
NAVET_COMPANY_PRESENTATION_LOCATION = "Escape"

# Fadderuke's own week-calendar color legend (see EventPage.calendar_legend's
# docstring) -- one entry per calendar_color actually used in
# FADDERUKE_SUB_EVENT_SPECS below.
FADDERUKE_LEGEND = [
    ("blue", "Relevant for studiet"),
    ("yellow", "Mat"),
    ("orange", "Alkoholfritt"),
    ("pink", "Med eller uten alkohol"),
    ("green", "Felles for hele MatNat"),
]

# (days-from-Fadderuke's-own-event_date, title, event_type, start "HH:MM",
# end "HH:MM", calendar_color) -- a full Mon-Fri Fadderuke programme, so
# EventPage.calendar_days has a realistic week to lay out instead of just
# the lone parent event. Titles that would otherwise repeat under the same
# parent (Lunsj, Forkurs, Grill n' chill) get a day/time qualifier purely to
# stay unique per (parent, slug, locale) -- see _get_or_create_page.
FADDERUKE_SUB_EVENT_SPECS = [
    (0, "Oppmøteregistrering", "academic", "09:00", "10:00", "blue"),
    (0, "Programvis opplegg (formiddag)", "academic", "10:00", "12:00", "blue"),
    (0, "Lunsj med fadderne", "social", "12:00", "13:00", "yellow"),
    (0, "Programvis opplegg (ettermiddag)", "academic", "13:00", "15:00", "blue"),
    (0, "Tale på universitetsplassen", "academic", "15:00", "16:00", "blue"),
    (0, "Grill n' chill (mandag)", "social", "16:00", "17:00", "yellow"),
    (0, "Quiz m/CYB", "social", "18:00", "19:00", "pink"),
    (0, "Brettspillkveld m/FUI", "social", "18:00", "21:00", "orange"),
    (1, "Forkurs (tirsdag)", "academic", "09:00", "12:30", "blue"),
    (1, "Lunsj (tirsdag)", "social", "12:00", "13:00", "yellow"),
    (1, "IFI-Olympiaden", "social", "13:00", "16:00", "orange"),
    (
        1,
        "Grill n' chill + Kåring av Olympiadevinner",
        "social",
        "16:00",
        "17:00",
        "yellow",
    ),
    (1, "Kickoff m/ Navet", "social", "17:30", "19:30", "pink"),
    (1, "Spillkveld m/Progsys", "social", "18:00", "21:00", "pink"),
    (1, "Musikkbingo m/MAKI", "social", "18:00", "21:00", "orange"),
    (2, "Forkurs (onsdag)", "academic", "09:00", "12:30", "blue"),
    (2, "Lunsj (onsdag)", "social", "12:00", "13:00", "yellow"),
    (2, "How to IFI m/FUI", "academic", "13:00", "14:00", "orange"),
    (2, "Introduksjon til foreningslivet m/FU", "social", "14:00", "15:00", "orange"),
    (2, "Foreningstorg", "social", "14:00", "16:00", "orange"),
    (2, "Grill n' chill (onsdag)", "social", "16:00", "17:00", "yellow"),
    (2, "Temafest m/Dagen@ifi", "social", "18:00", "21:00", "pink"),
    (3, "Lunsj + Speedfriending m/Fadderstyret", "social", "12:00", "13:00", "yellow"),
    (3, "Gaffaregatt m/Mikro", "social", "13:00", "16:00", "orange"),
    (3, "Volleyballturnering m/VIFI", "social", "13:00", "16:00", "orange"),
    (3, "Kaffesmaking m/CYB & kaffeforeningen", "social", "14:00", "16:00", "orange"),
    (3, "Grill n' chill (torsdag)", "social", "16:00", "17:00", "yellow"),
    (3, "Paint & Sip m/Defi", "social", "18:00", "21:00", "pink"),
    (
        3,
        "Realstart! Felles kveld for hele MatNat!",
        "social",
        "19:00",
        "22:00",
        "green",
    ),
    (4, "Lunsj (fredag)", "social", "12:00", "13:00", "yellow"),
    (4, "Shitty cars m/Sonen", "social", "13:00", "15:00", "orange"),
    (4, "Fotballturnering m/FIFI", "social", "13:00", "16:00", "orange"),
    (4, "2000-Meter m/Digitus", "social", "15:00", "16:00", "pink"),
    (4, "Grill n' chill + Kakefredag m/Progsys", "social", "16:00", "17:00", "yellow"),
    (4, "CTRL+ALT+DEL m/CYB", "social", "18:00", "21:00", "pink"),
]

# Shown in Fadderuke's own homepage dropdown (see
# EventPage.highlighted_sub_events) -- just the one event common to all of
# MatNat, not every sub-event.
FADDERUKE_HIGHLIGHTED_TITLES = {"Realstart! Felles kveld for hele MatNat!"}

# Student unions referenced by the "m/XXX" abbreviations in
# FADDERUKE_SUB_EVENT_SPECS's titles above -- created as minimal UnionPage
# children of the same Studentforeninger category as Testforening 1/2, with
# just enough fields filled in to be a real page (see _seed_fadderuke_unions).
FADDERUKE_UNION_SPECS = [
    "CYB",
    "FUI",
    "Progsys",
    "MAKI",
    "VIFI",
    "FU",
    "Mikro",
    "Defi",
    "Sonen",
    "FIFI",
    "Digitus",
    "Navet",
    "Fadderstyret",
    "Dagen@ifi",
]

# Real Peoply organization IDs, deliberately set on just these two (not
# every union above) -- a tester running seed_dev_data + sync_peoply_events
# locally should only ever hit Peoply's real API for a couple of unions,
# not every one of them. Production sets every real union's own ID by hand
# in wagtail-admin (see the link_peoply_organizations command for finding
# them), independent of this seed data entirely.
FADDERUKE_UNION_PEOPLY_IDS = {
    "Defi": "319a8d34-10c5-486d-81df-ee7ffaf7d1cd",
    "Navet": "94c34eb0-7de0-404a-b7af-595a2e54777d",
}

# Sub-event title -> [(union title, role), ...] for EventPage.related_unions
# -- "host" for the union directly named in the sub-event's own title,
# "contributor"/"collaborator" used on a couple of entries (Foreningstorg,
# Realstart!) to also demo those roles and multi-union entries. Sub-events
# not listed here (Lunsj, Grill n' chill, ...) are deliberately left
# union-less -- nobody specific "hosts" the cafeteria lunch.
FADDERUKE_SUB_EVENT_UNIONS = {
    "Oppmøteregistrering": [("Fadderstyret", "host")],
    "Programvis opplegg (formiddag)": [("Fadderstyret", "host")],
    "Programvis opplegg (ettermiddag)": [("Fadderstyret", "host")],
    "Tale på universitetsplassen": [("Fadderstyret", "host")],
    "Quiz m/CYB": [("CYB", "host")],
    "Brettspillkveld m/FUI": [("FUI", "host")],
    "Forkurs (tirsdag)": [("Fadderstyret", "host")],
    "IFI-Olympiaden": [("Fadderstyret", "host")],
    "Kickoff m/ Navet": [("Navet", "host")],
    "Spillkveld m/Progsys": [("Progsys", "host")],
    "Musikkbingo m/MAKI": [("MAKI", "host")],
    "Forkurs (onsdag)": [("Fadderstyret", "host")],
    "How to IFI m/FUI": [("FUI", "host")],
    "Introduksjon til foreningslivet m/FU": [("FU", "host")],
    "Foreningstorg": [
        ("CYB", "contributor"),
        ("FUI", "contributor"),
        ("Progsys", "contributor"),
        ("VIFI", "contributor"),
    ],
    "Temafest m/Dagen@ifi": [("Dagen@ifi", "host")],
    "Lunsj + Speedfriending m/Fadderstyret": [("Fadderstyret", "host")],
    "Gaffaregatt m/Mikro": [("Mikro", "host")],
    "Volleyballturnering m/VIFI": [("VIFI", "host")],
    "Kaffesmaking m/CYB & kaffeforeningen": [("CYB", "host")],
    "Paint & Sip m/Defi": [("Defi", "host")],
    "Realstart! Felles kveld for hele MatNat!": [
        ("Fadderstyret", "host"),
        ("CYB", "collaborator"),
        ("Progsys", "collaborator"),
    ],
    "Shitty cars m/Sonen": [("Sonen", "host")],
    "Fotballturnering m/FIFI": [("FIFI", "host")],
    "2000-Meter m/Digitus": [("Digitus", "host")],
    "Grill n' chill + Kakefredag m/Progsys": [("Progsys", "host")],
    "CTRL+ALT+DEL m/CYB": [("CYB", "host")],
}

# (title, intro, body heading, body paragraph) -- demo content for the
# "Ny Ifi Student?" category (see _seed_new_student_articles), so the
# homepage's "New Student?" dropdown (navbar/navbar.html) has real
# articles/thumbnails to show instead of its "No articles yet" fallback.
NEW_STUDENT_ARTICLE_SPECS = [
    (
        "Adgangskort",
        "Alt du trenger å vite om å skaffe adgangskort til Ifi.",
        "Hvordan skaffe adgangskort",
        "I teorien går det an å være student uten adgangskort. Men det blir "
        "fort veldig upraktisk og du bør skaffe deg et så fort som mulig.",
    ),
    (
        "Sjekkliste for nye Ifi-studenter",
        "En sjekkliste over det aller viktigste du bør ordne som ny student.",
        "Sjekkliste",
        "Som ny student er det en del å gjøre, men heldigvis trenger du "
        "bare å gjøre de fleste av disse tingene én gang.",
    ),
    (
        "Nyttige verktøy det er skjekt å vite om",
        "En oversikt over verktøy og tjenester som gjør studiehverdagen enklere.",
        "Verktøy",
        "Det finnes mange nyttige verktøy og tjenester som Ifi-studenter "
        "bruker i studiehverdagen. Her er noen av de mest brukte.",
    ),
]

BANNER_TEXT = "Welcome to your local dev server"

LOREM_IPSUM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat."
)

# nb -> en for every translatable string this script writes. Fed through
# wagtail_localize's real PO import/export pipeline (see _translate_page)
# rather than just hand-writing a second copy of every field. Anything not
# listed here (image files, choice fields, urls, the placeholder name/email)
# falls back to the source-language value untouched.
TRANSLATIONS = {
    "Artikkler": "Articles",
    "Nyheter": "News",
    "Informasjonsartikkler": "Info Articles",
    "Praktisk": "Practical",
    "Akademisk": "Academic",
    "Sosialt": "Social",
    "Hjelp": "Help",
    "IfiPlattform": "IfiPlatform",
    "Testartikkel": "Test Article",
    "Ifi verktøy": "Ifi Tools",
    "Test-verktøy": "Test Tool",
    "UiO verktøy": "UiO Tools",
    "Nøstet test-verktøy": "Nested test tool",
    'Et nøstet test-verktøy generert av seed-scriptet, for å vise Ifi verktøy sin "vis nøstede verktøy"-innstilling.': 'A nested test tool generated by the seed script, to demonstrate Ifi Tools\' "show nested tools" setting.',
    "Studentforeninger": "Student Unions",
    "Testforening 1": "Test Union 1",
    "Testforening 2": "Test Union 2",
    "Den Ekstremt Lange Studentforeningen for Informatikkstudenter med "
    "Spesiell Interesse for Kunstig Intelligens og Maskinlæring": (
        "The Extremely Long Student Union for Computer Science Students "
        "with a Special Interest in Artificial Intelligence and Machine Learning"
    ),
    "Siste nytt": "Latest News",
    "Nyhetsartikkel 1": "News Article 1",
    "Nyhetsartikkel 2": "News Article 2",
    "Nyhetsartikkel 3": "News Article 3",
    "Nyhetsartikkel 4": "News Article 4",
    "Om denne testartikkelen": "About this test article",
    "En test-artikkel generert av seed-scriptet.": "A test article generated by the seed script.",
    "En test-nyhetsartikkel generert av seed-scriptet.": "A test news article generated by the seed script.",
    "Dette er en automatisk generert test-artikkel laget av seed-scriptet for lokal utvikling. Innholdet er kun til testformål.": "This is an automatically generated test article created by the seed script for local development. The content is for testing purposes only.",
    "Test-formål generert av seed-scriptet.": "Test purpose generated by the seed script.",
    "Test-aktiviteter generert av seed-scriptet.": "Test activities generated by the seed script.",
    "Leder": "Chair",
    "Et test-verktøy generert av seed-scriptet.": "A test tool generated by the seed script.",
    "Arrangementer": "Events",
    "Fadderuke": "Fadderuke",
    "Bar til bar": "Bar crawl",
    "Frist for funk-oppmelding for Dagen@IFI": "Deadline: Dagen@IFI committee signup",
    "DNB Bedriftspresentasjon med Navet": "DNB company presentation with Navet",
    # Fadderuke's own calendar-color legend (FADDERUKE_LEGEND).
    "Relevant for studiet": "Relevant to Studies",
    "Mat": "Food",
    "Alkoholfritt": "Non-alcoholic",
    "Med eller uten alkohol": "With or without alcohol",
    "Felles for hele MatNat": "Common to the entire MatNat",
    # Fadderuke sub-events (FADDERUKE_SUB_EVENT_SPECS).
    "Oppmøteregistrering": "Check-in",
    "Programvis opplegg (formiddag)": "Programme-specific session (morning)",
    "Lunsj med fadderne": "Lunch with the mentors",
    "Programvis opplegg (ettermiddag)": "Programme-specific session (afternoon)",
    "Tale på universitetsplassen": "Speech at the University Square",
    "Grill n' chill (mandag)": "Grill n' chill (Monday)",
    "Quiz m/CYB": "Quiz w/CYB",
    "Brettspillkveld m/FUI": "Board game night w/FUI",
    "Forkurs (tirsdag)": "Pre-course (Tuesday)",
    "Lunsj (tirsdag)": "Lunch (Tuesday)",
    "IFI-Olympiaden": "The IFI Olympics",
    "Grill n' chill + Kåring av Olympiadevinner": "Grill n' chill + Olympics winner announcement",
    "Kickoff m/ Navet": "Kickoff w/ Navet",
    "Spillkveld m/Progsys": "Games night w/Progsys",
    "Musikkbingo m/MAKI": "Music bingo w/MAKI",
    "Forkurs (onsdag)": "Pre-course (Wednesday)",
    "Lunsj (onsdag)": "Lunch (Wednesday)",
    "How to IFI m/FUI": "How to IFI w/FUI",
    "Introduksjon til foreningslivet m/FU": "Intro to student union life w/FU",
    "Foreningstorg": "Student union fair",
    "Grill n' chill (onsdag)": "Grill n' chill (Wednesday)",
    "Temafest m/Dagen@ifi": "Theme party w/Dagen@ifi",
    "Lunsj + Speedfriending m/Fadderstyret": "Lunch + Speedfriending w/the Mentor Committee",
    "Gaffaregatt m/Mikro": "Gaffaregatt w/Mikro",
    "Volleyballturnering m/VIFI": "Volleyball tournament w/VIFI",
    "Kaffesmaking m/CYB & kaffeforeningen": "Coffee tasting w/CYB & the coffee student union",
    "Grill n' chill (torsdag)": "Grill n' chill (Thursday)",
    "Paint & Sip m/Defi": "Paint & Sip w/Defi",
    "Realstart! Felles kveld for hele MatNat!": "Realstart! Joint evening for all of MatNat!",
    "Lunsj (fredag)": "Lunch (Friday)",
    "Shitty cars m/Sonen": "Shitty cars w/Sonen",
    "Fotballturnering m/FIFI": "Football tournament w/FIFI",
    "2000-Meter m/Digitus": "2000m race w/Digitus",
    "Grill n' chill + Kakefredag m/Progsys": "Grill n' chill + Cake Friday w/Progsys",
    "CTRL+ALT+DEL m/CYB": "CTRL+ALT+DEL w/CYB",
    # Fadderuke-hosting unions (FADDERUKE_UNION_SPECS) -- most are
    # abbreviations/proper names left as-is; only Fadderstyret has a real
    # English equivalent worth translating.
    "Fadderstyret": "The Mentor Committee",
    "En studentforening ved Ifi generert av seed-scriptet.": "A student union at Ifi generated by the seed script.",
    # "Ny Ifi Student?" category + its demo articles (NEW_STUDENT_ARTICLE_SPECS).
    "Ny Ifi Student?": "New Student?",
    "Her er alt du skulle trenge som en ny Ifi Student!": "Here's everything you should need as a new Ifi student!",
    "Adgangskort": "Access card",
    "Alt du trenger å vite om å skaffe adgangskort til Ifi.": "Everything you need to know about getting an access card for Ifi.",
    "Hvordan skaffe adgangskort": "How to get an access card",
    "I teorien går det an å være student uten adgangskort. Men det blir fort veldig upraktisk og du bør skaffe deg et så fort som mulig.": "In theory it's possible to be a student without an access card. But it quickly gets very impractical, so you should get one as soon as possible.",
    "Sjekkliste for nye Ifi-studenter": "Checklist for new Ifi students",
    "En sjekkliste over det aller viktigste du bør ordne som ny student.": "A checklist of the most important things to sort out as a new student.",
    "Sjekkliste": "Checklist",
    "Som ny student er det en del å gjøre, men heldigvis trenger du bare å gjøre de fleste av disse tingene én gang.": "As a new student there's quite a bit to do, but luckily you only need to do most of these things once.",
    "Nyttige verktøy det er skjekt å vite om": "Useful tools worth knowing about",
    "En oversikt over verktøy og tjenester som gjør studiehverdagen enklere.": "An overview of tools and services that make everyday student life easier.",
    "Verktøy": "Tools",
    "Det finnes mange nyttige verktøy og tjenester som Ifi-studenter bruker i studiehverdagen. Her er noen av de mest brukte.": "There are many useful tools and services Ifi students use day to day. Here are some of the most commonly used ones.",
}

ARTICLE_BODY = [
    ("heading", {"text": "Om denne testartikkelen", "level": "h2"}),
    (
        "paragraph",
        {
            "text": RichText(
                "<p>Dette er en automatisk generert test-artikkel laget av "
                "seed-scriptet for lokal utvikling. Innholdet er kun til "
                "testformål.</p>"
            )
        },
    ),
]

BOARD_MESSAGE_SPECS = [
    {
        "title": "Lorem Ipsum 1",
        "sender_name": "Lorem Ipsum",
        "display_seconds": 30,
        # short enough that the message body shouldn't need to scroll
        "body": "<p>Lorem ipsum dolor sit amet.</p>",
    },
    {
        "title": "Lorem Ipsum 2",
        "sender_name": "Dolor Sit",
        "display_seconds": 45,
        # long enough to just overflow the fixed-height card, so scrolling kicks in
        "body": "".join(f"<p>{LOREM_IPSUM}</p>" for _ in range(2)),
    },
    {
        "title": "Lorem Ipsum 3",
        "sender_name": "Amet Consectetur",
        "display_seconds": 60,
        # several paragraphs, clearly needs a lot of scrolling
        "body": "".join(f"<p>{LOREM_IPSUM}</p>" for _ in range(5)),
    },
]
