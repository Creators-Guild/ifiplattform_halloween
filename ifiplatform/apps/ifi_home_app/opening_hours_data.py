"""Opening hours for the home page's right column (the "Open now" box).

Each place has a name and its hours for every weekday, Monday first: a pair
("08:00", "16:00") for open from 08:00 to 16:00, or None for closed all day.
A closing time before the opening time means it closes after midnight:
("20:00", "02:00") is open until 2 at night.

The hours below are placeholders until an event issue fills in the real
ones."""

PLACES = [
    {
        "name": "Informatikkbiblioteket",
        "hours": [("08:00", "18:00")] * 4 + [("08:00", "16:00"), None, None],
    },
    {
        "name": "Kantina, Ole-Johan Dahls hus",
        "hours": [("10:00", "15:00")] * 5 + [None, None],
    },
    {
        "name": "Lesesalen, Ole-Johan Dahls hus",
        "hours": [("07:00", "01:00")] * 7,
    },
    {
        "name": "Ekspedisjonen, Ifi",
        "hours": [("09:00", "15:00")] * 5 + [None, None],
    },
]
