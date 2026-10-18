"""Where the moon is in its cycle of about 29.5 days, for the moon on every
page."""

from datetime import datetime, timezone

SYNODIC_MONTH = 29.530588853  # days from one new moon to the next
KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)


def phase(moment):
    """0 is new moon, 0.5 full moon, and just under 1 almost new again.
    moment: a datetime with a time zone."""
    days = (moment - KNOWN_NEW_MOON).total_seconds() / 86400
    return (days % SYNODIC_MONTH) / SYNODIC_MONTH


def shadow_offset(moon_phase):
    """Where the shadow sits, in % of the moon's width from its middle: 0
    covers the whole moon (new moon), -100 or 100 is clear of it (full
    moon). Seen from Norway the moon grows from the right, so a growing
    moon's shadow moves off to the left."""
    if moon_phase <= 0.5:
        return round(-200 * moon_phase)
    return round(200 * (1 - moon_phase))
