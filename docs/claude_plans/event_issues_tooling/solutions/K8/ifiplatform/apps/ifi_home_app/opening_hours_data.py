"""Opening hours for the home page's right column (the "Open now" box).

Each place has a name and its hours for every weekday, Monday first: a pair
("08:00", "16:00") for open from 08:00 to 16:00, or None for closed all day.
A closing time before the opening time means it closes after midnight:
("20:00", "02:00") is open until 2 at night.

Checked on 18 October 2026, on the pages below. Hours change between
semesters and in the holidays, so check again now and then:
- https://www.ub.uio.no/bibliotekene/index.html#informatikk
- https://sio.no/en/food-and-beverage/spisesteder/Union%20Blindern"""

PLACES = [
    {
        "name": "Informatikkbiblioteket, staffed",
        "hours": [("10:00", "14:00")] * 5 + [None, None],
    },
    {
        "name": "Informatikkbiblioteket, with UiO card",
        "hours": [("05:00", "24:00")] * 7,
    },
    {
        "name": "Union 371 Blindern",
        "hours": [("11:00", "18:00")] * 5 + [None, None],
    },
]
