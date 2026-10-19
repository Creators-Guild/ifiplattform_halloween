"""Opening hours for the home page's right column (the "Open now" box).

Each place has a name and its hours for every weekday, Monday first: a pair
("08:00", "16:00") for open from 08:00 to 16:00, or None for closed all day.
A closing time before the opening time means it closes after midnight:
("20:00", "02:00") is open until 2 at night.
"""

PLACES = [
    {
        "name": "Ole-Johan spiseri, Ifi",
        "hours": [("09:00", "16:00")] * 4 + [("09:00", "15:00")] + [None, None],
    },
    {
        "name": "Escape Kafé, Ifi",
        "hours": [("10:00", "15:30")] * 5 + [None] * 2,
    },
    {
        "name": "Informatikkbiblioteket",
        "hours": [("10:00", "14:00")] * 5 + [None, None],
    },
    {
        "name": "Informatikkbiblioteket (UiO kort & kode)",
        "hours": [("05:00", "24:00")] * 7,
    },
    {
        "name": "Ifi Studentekspedisjonen i 4. etg, Ifi",
        "hours": [("12:00", "15:00")] * 5 + [None, None],
    },
    {
        "name": "Frederikke spiseri, Frederikke",
        "hours": [("11:00", "18:00")] * 4 + [("11:00", "16:30")] + [None, None],
    },
     {
        "name": " HumSam-biblioteket, Georg Sverdrups hus",
        "hours": [("08:00", "22:00")] * 5 + [("10:00", "18:00")] * 2,
    },
]
